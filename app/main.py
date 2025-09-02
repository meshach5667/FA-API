from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine, get_db
from app.api import (
    explore,
    check_in,
    check_out,
    scan_check_in,
    scan_check_out,
    auth,
    booking,
    activities,
    communities,
    notifications,
    payment,
    rewards,
    members,
    reconciliation,
    schedule,
    transaction,
    groups,
    analytics,
    business_auth,
    admin,
    advertisements,
)
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from app.api.rewards_seed import seed_rewards

app = FastAPI(
    title="FitAccess API",
    description="Backend for FitAccess - Access Premium Gyms With One Pass",
    version="1.0.0"
)
# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Register all route modules with a prefix
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(business_auth.router, prefix="/business-auth", tags=["Business Auth"])
app.include_router(explore.router, prefix="/explore", tags=["Explore"])
app.include_router(check_in.router, prefix="/check-in", tags=["Check-In"])
app.include_router(check_out.router, prefix="/check-out", tags=["Check-Out"])
app.include_router(scan_check_in.router, prefix="/scan-check-in", tags=["Scan Check-In"])
app.include_router(scan_check_out.router, prefix="/scan-check-out", tags=["Scan Check-Out"])
app.include_router(booking.router, prefix="/booking", tags=["Booking"])
app.include_router(activities.router, prefix="/activities", tags=["Activities"])
app.include_router(communities.router, prefix="/communities", tags=["Communities"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(rewards.router, prefix="/rewards", tags=["Rewards"])
app.include_router(members.router, prefix="/members", tags=["Members"])
app.include_router(admin.router, prefix="/admin", tags=["SuperAdmin"])
app.include_router(advertisements.router, prefix="/admin/advertisements", tags=["Advertisements"])

app.include_router(payment.router, prefix="/payment", tags=["Payment"])
app.include_router(reconciliation.router, prefix="/reconciliation", tags=["Reconciliation"])
app.include_router(schedule.router, prefix="/schedule", tags=["Schedule"])
app.include_router(transaction.router, prefix="/transaction", tags=["Transaction"])
app.include_router(groups.router, prefix="/groups", tags=["Groups"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

# app.include_router(payment.router, prefix="/payment", tags=["Payment"])
# app.include_router(members.router, prefix="/members", tags=["Members"])
# app.include_router(reconciliation.router, prefix="/reconciliation", tags=["Reconciliation"])
# app.include_router(schedule.router, prefix="/schedule", tags=["Schedule"])
# app.include_router(transaction.router, prefix="/transaction", tags=["Transaction"])
# app.include_router(groups.router, prefix="/groups", tags=["Groups"])
# app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
# app.include_router(history.router, prefix="/history", tags=["History"])

@app.get("/", tags=["Health Check"])
async def root():
    return {"message": "Welcome to FitAccess API"}

@app.on_event("startup")
async def startup_event():
    print("🚀 FitAccess API is running and ready to accept requests.")
    # Create all tables (models are already imported via API routers)
    Base.metadata.create_all(bind=engine)
    # Seed rewards
    db = next(get_db())
    seed_rewards(db)

@app.middleware("http")
async def catch_all_404(request: Request, call_next):
    response = await call_next(request)
    if (response.status_code == 404):
        print(f"404 Not Found: {request.method} {request.url}")
    return response
