from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import joblib
import numpy as np
import pandas as pd
from typing import List, Optional
import os

# Initialize FastAPI app
app = FastAPI(
    title="Vehicle Cost Prediction API",
    description="API to predict vehicle costs using consumption, distance, and energy cost",
    version="2.0.0"
)

# Load the trained model and feature columns at startup
try:
    model = joblib.load('./models/best_model.pkl')
    feature_cols = joblib.load('./models/feature_columns.pkl')
    print(f"Model loaded successfully with features: {feature_cols}")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None
    feature_cols = None

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
    usuario: str
    consumo_MIN: float
    consumo_MAX: float
    total_km: float
    energia_kWh: float
    coste_energetico_vehiculo: float
    prediction: float

class BatchPredictionRequest(BaseModel):
    data: List[PredictionRequest]
    
    class Config:
        schema_extra = {
            "example": {
                "data": [
                    {
                        "usuario": "user123",
                        "consumo_MIN": 0.15,
                        "consumo_MAX": 0.20,
                        "total_km": 25000.0,
                        "energia_kWh": 0.25
                    },
                    {
                        "usuario": "user456",
                        "consumo_MIN": 0.18,
                        "consumo_MAX": 0.22,
                        "total_km": 30000.0,
                        "energia_kWh": 0.28
                    }
                ]
            }
        }

class BatchPredictionResponse(BaseModel):
    predictions: List[dict]

def calculate_coste_energetico(consumo_MIN: float, consumo_MAX: float, 
                                total_km: float, energia_kWh: float) -> float:
    """
    Calculate energy cost for the vehicle
    Formula: coste_energetico_vehiculo = ((consumo_MIN + consumo_MAX) / 2) * total_km * energia_kWh
    """
    consumo_promedio = (consumo_MIN + consumo_MAX) / 2
    coste = consumo_promedio * total_km * energia_kWh
    return coste



# Single prediction endpoint
@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # Calculate coste_energetico_vehiculo at router level
        coste_energetico_vehiculo = calculate_coste_energetico(
            request.consumo_MIN,
            request.consumo_MAX,
            request.total_km,
            request.energia_kWh
        )
        
        # Prepare input data with exact feature names
        input_data = pd.DataFrame([[
            coste_energetico_vehiculo,
            request.total_km
        ]], columns=['coste_energetico_vehiculo', 'total_km'])
        
        # Make prediction
        prediction = model.predict(input_data)[0]
        
        return PredictionResponse(
            usuario=request.usuario,
            consumo_MIN=request.consumo_MIN,
            consumo_MAX=request.consumo_MAX,
            total_km=request.total_km,
            energia_kWh=request.energia_kWh,
            coste_energetico_vehiculo=float(coste_energetico_vehiculo),
            prediction=float(prediction)
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")

# Batch prediction endpoint
@app.post("/predict_batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictionRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # Calculate coste_energetico for each item
        costes_energeticos = []
        for item in request.data:
            coste = calculate_coste_energetico(
                item.consumo_MIN,
                item.consumo_MAX,
                item.total_km,
                item.energia_kWh
            )
            costes_energeticos.append(coste)
        
        # Prepare input data
        input_data = pd.DataFrame([
            [coste, item.total_km]
            for coste, item in zip(costes_energeticos, request.data)
        ], columns=['coste_energetico_vehiculo', 'total_km'])
        
        # Make predictions
        predictions = model.predict(input_data)
        
        # Return sum of all consumo en litros
        total_consumo = float(predictions)
        
        return BatchPredictionResponse(consumo_litros=total_consumo)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Batch prediction error: {str(e)}")

