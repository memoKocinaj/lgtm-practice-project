import os
import time
import random
import logging
import requests
from fastapi import FastAPI, Response, HTTPException
from opentelemetry.instrumentation.logging import LoggingInstrumentor

LoggingInstrumentor().instrument(set_logging_format=True)

# Configure standard Python logging to output JSON-like structure for Loki
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()
SERVICE_NAME = os.getenv("SERVICE_NAME", "unknown-service")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8002")

@app.get("/health")
def health():
    return {"status": "healthy", "service": SERVICE_NAME}

# --- ORDER SERVICE ENDPOINTS ---
if SERVICE_NAME == "order-service":
    @app.post("/order")
    def create_order():
        order_id = random.randint(1000, 9999)
        logger.info(f"Received request to create order #{order_id}")
        
        # Call the payment service
        try:
            logger.info(f"Forwarding order #{order_id} to payment service...")
            response = requests.post(f"{PAYMENT_SERVICE_URL}/payment", json={"order_id": order_id})
            
            if response.status_code != 200:
                logger.error(f"Payment failed for order #{order_id} with status {response.status_code}")
                raise HTTPException(status_code=500, detail="Payment processing failed")
                
            logger.info(f"Order #{order_id} successfully processed and completed!")
            return {"status": "Order Placed", "order_id": order_id}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to payment service: {str(e)}")
            raise HTTPException(status_code=503, detail="Payment service unavailable")

# --- PAYMENT SERVICE ENDPOINTS ---
elif SERVICE_NAME == "payment-service":
    @app.post("/payment")
    def process_payment(response: Response):
        # 1. Simulate Chaos - 15% chance of severe delay
        if random.random() < 0.15:
            logger.warning("Simulating heavy database load... delaying request.")
            time.sleep(2.5)
            
        # 2. Simulate Chaos - 15% chance of internal server error
        if random.random() < 0.15:
            logger.error("Database connection timeout error inside payment system!")
            response.status_code = 500
            return {"error": "Internal Database Timeout"}
            
        logger.info("Payment captured successfully.")
        return {"status": "success"}