#!/bin/bash
cd /var/www/havo-sifati
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8000
