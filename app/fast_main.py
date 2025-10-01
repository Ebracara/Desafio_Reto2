from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import joblib

# Initialize FastAPI app
app = FastAPI(
    title="Vehicle Cost Prediction API",
    description="API to predict vehicle consumption and costs",
    version="2.0.0"
)

# Load both models at startup
try:
    consumption_model = joblib.load('./models/best_model.pkl')
    price_model = joblib.load('./models/best_model2.pkl')
    print("Models loaded successfully")
except Exception as e:
    print(f"Error loading models: {e}")
    consumption_model = None
    price_model = None

# ========== Pydantic Models ==========
class PredictionRequest(BaseModel):
    usuario: str = Field(..., description="User identifier")
    consumo_MIN: float = Field(..., description="Minimum consumption (kWh/km)", gt=0)
    consumo_MAX: float = Field(..., description="Maximum consumption (kWh/km)", gt=0)
    total_km: float = Field(..., description="Total kilometers", gt=0)
    energia_kWh: float = Field(..., description="Energy cost per kWh (€/kWh)", gt=0)
    
    class Config:
        schema_extra = {
            "example": {
                "usuario": "user123",
                "consumo_MIN": 0.15,
                "consumo_MAX": 0.20,
                "total_km": 25000.0,
                "energia_kWh": 0.25
            }
        }
class PredictionCosteRequest(PredictionRequest):
    nombre_carburante: str = Field(..., description="nombre de carburante")
    class Config:
        schema_extra = {
            "example": {
                "usuario": "user123",
                "consumo_MIN": 0.15,
                "consumo_MAX": 0.20,
                "total_km": 25000.0,
                "energia_kWh": 0.25,
                "nombre_carburante": "Biodiesel"
            }
        }
class ConsumptionResponse(BaseModel):
    consumo_litros: float

class CostResponse(BaseModel):
    coste_mensual: float

# ========== Helper Function ==========
def calculate_coste_energetico(consumo_MIN: float, consumo_MAX: float, 
                                total_km: float, energia_kWh: float) -> float:
    """
    Calculate energy cost for the vehicle
    Formula: coste_energetico_vehiculo = ((consumo_MIN + consumo_MAX) / 2) * total_km * energia_kWh/100
    """
    consumo_promedio = (consumo_MIN + consumo_MAX) / 200
    coste = consumo_promedio * total_km * energia_kWh
    return coste

# ========== Endpoint 1: Predict Consumption ==========
@app.post("/predict/consumption", response_model=ConsumptionResponse)
async def predict_consumption(request: PredictionRequest):
    """
    Predicts fuel consumption in liters using Model 1
    """
    if consumption_model is None:
        raise HTTPException(status_code=500, detail="Consumption model not loaded")
    
    try:
        # Calculate coste_energetico_vehiculo
        coste_energetico_vehiculo = calculate_coste_energetico(
            request.consumo_MIN,
            request.consumo_MAX,
            request.total_km,
            request.energia_kWh
        )
        
        # Prepare input: [coste_energetico_vehiculo, total_km]
        input_data = [[coste_energetico_vehiculo, request.total_km]]
        
        # Make prediction
        consumo_litros = float(consumption_model.predict(input_data)[0])
        
        return ConsumptionResponse(
            consumo_litros=consumo_litros
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")
import pandas as pd

# ========== Fuel Type Encoding (add at top of file) ==========
# TODO: Replace these values with your actual encoding from training
FUEL_ENCODING = {
    "Biodiesel":0,
    "Bioetanol":1,
    "Gas Natural Comprimido":2,
    "Gas Natural Licuado":3,
    "Gases licuados del petróleo":4,
    "Gasoleo A":5,
    "Gasoleo B":6,
    "Gasoleo Premium":7,
    "Gasolina 95 E5":8,
    "Gasolina 95 E5 Premium":9,
    "Gasolina 98 E5":10
}

# ========== Endpoint 2: Predict Cost ==========
@app.post("/predict/cost", response_model=CostResponse)
async def predict_cost(request: PredictionCosteRequest):
    """
    Predicts monthly cost:
    1. Model 1 predicts consumption (liters)
    2. Model 2 predicts price per liter
    3. Returns: consumption * price = monthly cost
    """
    if consumption_model is None or price_model is None:
        raise HTTPException(status_code=500, detail="Models not loaded")
    
    try:
        # Validate and encode fuel type
        if request.nombre_carburante not in FUEL_ENCODING:
            raise ValueError(
                f"Unknown fuel type: {request.nombre_carburante}. "
                f"Valid types: {list(FUEL_ENCODING.keys())}"
            )
        
        enc_nombre_carburante = FUEL_ENCODING[request.nombre_carburante]
        
        # Calculate coste_energetico_vehiculo
        coste_energetico_vehiculo = calculate_coste_energetico(
            request.consumo_MIN,
            request.consumo_MAX,
            request.total_km,
            request.energia_kWh
        )
        
        # Prepare input for Model 1: [coste_energetico_vehiculo, total_km]
        input_data = [[coste_energetico_vehiculo, request.total_km]]
        
        # Predict consumption with Model 1
        consumo_litros = float(consumption_model.predict(input_data)[0])
        
        # Prepare input for Model 2 with ENCODED column name
        input_data_price = pd.DataFrame(
            [[enc_nombre_carburante, request.energia_kWh]],
            columns=['enc_nombre_carburante', 'energia_kWh']
        )

        # Predict price per liter with Model 2
        precio_litro = float(price_model.predict(input_data_price)[0])
        
        # Calculate monthly cost
        coste_mensual = consumo_litros * precio_litro
        
        return CostResponse(
            coste_mensual=coste_mensual
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")