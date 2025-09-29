from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import joblib

# Initialize FastAPI app
app = FastAPI(
    title="Vehicle Cost Prediction API",
    description="API to predict vehicle costs using consumption, distance, and energy cost",
    version="2.0.0"
)

# Load the trained model at startup
try:
    model = joblib.load('./models/best_model.pkl')
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# Pydantic models for request/response
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

class PredictionResponse(BaseModel):
    consumo_litros: float

def calculate_coste_energetico(consumo_MIN: float, consumo_MAX: float, 
                                total_km: float, energia_kWh: float) -> float:
    """
    Calculate energy cost for the vehicle
    Formula: coste_energetico_vehiculo = ((consumo_MIN + consumo_MAX) / 2) * total_km * energia_kWh/100
    """
    consumo_promedio = (consumo_MIN + consumo_MAX) / 200
    coste = consumo_promedio * total_km * energia_kWh
    return coste

# Prediction endpoint
@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
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
        
        # Make prediction - get single value
        prediction = model.predict(input_data)[0]
        
        return PredictionResponse(consumo_litros=float(prediction))
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")
