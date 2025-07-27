# from fastapi import APIRouter, HTTPException, Query

# from packages.scraper.src.index import run_all_scrapers, run_scraper_by_name
# from apps.api.utils.threading import run_in_thread, service_manager
# from packages.db.db import SessionLocal
# from packages.models.integrations import Integration

# router = APIRouter()

# @router.post("/start-scraper")
# def trigger_scraper():
#     try:
#         # Check if scraper is already running
#         if service_manager.is_service_running("scraper"):
#             return {
#                 "status": "Scraper is already running",
#                 "message": "Please wait for the current scraping process to complete"
#             }
        
#         service_id = run_in_thread(
#             run_all_scrapers,
#             service_name="scraper",
#             description="Running all configured scrapers"
#         )
        
#         return {
#             "status": "Scraper started",
#             "service_id": service_id,
#             "message": "Scraping process started in background"
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/start-scraper/{scraper_name}")
# def trigger_single_scraper(scraper_name: str):
#     """Start a single scraper by name in a background thread."""
#     try:
#         # Check if this specific scraper is already running
#         if service_manager.is_service_running(f"scraper-{scraper_name}"):
#             return {
#                 "status": f"Scraper '{scraper_name}' is already running",
#                 "message": "Please wait for the current scraping process to complete"
#             }
        
#         service_id = run_in_thread(
#             lambda: run_scraper_by_name(scraper_name),
#             service_name=f"scraper-{scraper_name}",
#             description=f"Running {scraper_name} scraper"
#         )
        
#         return {
#             "status": f"Scraper '{scraper_name}' started",
#             "service_id": service_id,
#             "message": f"Scraper '{scraper_name}' started in background"
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/list-scrapers")
# def list_scrapers():
#     """Return the names of all connected scrapers (integrations)."""
#     session = SessionLocal()
#     try:
#         integrations = session.query(Integration).filter_by(is_connected=True).all()
#         names = [integration.name for integration in integrations]
#         return {"scrapers": names}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         session.close()

# @router.get("/status")
# def get_scraper_status():
#     """Get the current status of background scraping services."""
#     try:
#         running_services = service_manager.get_running_services()
#         scraper_services = [
#             service for service in running_services 
#             if service["name"].startswith("scraper")
#         ]
        
#         return {
#             "scraper_services": scraper_services,
#             "total_running": len(scraper_services),
#             "is_running": len(scraper_services) > 0
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
