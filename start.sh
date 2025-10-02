#!/bin/bash
uvicorn app.fast_main:app --host 0.0.0.0 --port 8000 &
streamlit run app/streamlit_app.py --server.port 8501