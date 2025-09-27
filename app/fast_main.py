
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import pandas as pd
from typing import List
import os

# Initialize FastAPI app
app = FastAPI(
    title="Vehicle Cost Prediction API",
    description="API to predict vehicle costs using energy cost and total km",
    version="1.0.0"
)

# Load the trained model and feature columns at startup
try:
    model = joblib.load('../models/best_model.pkl')
    feature_cols = joblib.load('../models/feature_columns.pkl')
    print(f"Model loaded successfully with features: {feature_cols}")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None
    feature_cols = None

# Pydantic models for request/response
class PredictionRequest(BaseModel):
    coste_energetico_vehiculo: float
    total_km: float
    
    class Config:
        schema_extra = {
            "example": {
                "coste_energetico_vehiculo": 150.5,
                "total_km": 25000.0
            }
        }

class PredictionResponse(BaseModel):
    prediction: float
    coste_energetico_vehiculo: float
    total_km: float
    
class BatchPredictionRequest(BaseModel):
    data: List[PredictionRequest]
    
    class Config:
        schema_extra = {
            "example": {
                "data": [
                    {"coste_energetico_vehiculo": 150.5, "total_km": 25000.0},
                    {"coste_energetico_vehiculo": 200.0, "total_km": 30000.0}
                ]
            }
        }

class BatchPredictionResponse(BaseModel):
    predictions: List[dict]

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "Vehicle Cost Prediction API", 
        "status": "running",
        "model_loaded": model is not None
    }

# Single prediction endpoint
@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # Prepare input data with exact feature names
        input_data = pd.DataFrame([[
            request.coste_energetico_vehiculo,
            request.total_km
        ]], columns=['coste_energetico_vehiculo', 'total_km'])
        
        # Make prediction
        prediction = model.predict(input_data)[0]
        
        return PredictionResponse(
            prediction=float(prediction),
            coste_energetico_vehiculo=request.coste_energetico_vehiculo,
            total_km=request.total_km
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")

# Batch prediction endpoint
@app.post("/predict_batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictionRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # Prepare input data
        input_data = pd.DataFrame([
            [item.coste_energetico_vehiculo, item.total_km] 
            for item in request.data
        ], columns=['coste_energetico_vehiculo', 'total_km'])
        
        # Make predictions
        predictions = model.predict(input_data)
        
        # Format response with input values and predictions
        results = []
        for i, item in enumerate(request.data):
            results.append({
                "coste_energetico_vehiculo": item.coste_energetico_vehiculo,
                "total_km": item.total_km,
                "prediction": float(predictions[i])
            })
        
        return BatchPredictionResponse(predictions=results)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Batch prediction error: {str(e)}")
