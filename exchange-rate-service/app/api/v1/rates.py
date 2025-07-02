from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services.rate_service import RateService
from app.services.rate_fetcher import RateFetcher
from app.schemas.rate import (
    RateRequest, RateCalculationRequest, ExchangeRateResponse,
    RateCalculationResponse, MultipleRatesResponse, RateHistoryResponse,
    BulkRateUpdateResponse
)
from app.utils.response import SuccessResponse, ErrorResponse
from app.utils.exceptions import RateNotFoundError, ValidationError

router = APIRouter()

@router.get("/current", response_model=SuccessResponse[ExchangeRateResponse])
async def get_current_rate(
    currency: str = Query(..., description="Currency code (e.g., USD, EUR)"),
    db: Session = Depends(get_db)
):
    """Get current exchange rate for a specific currency"""
    try:
        rate_service = RateService(db)
        rate = await rate_service.get_current_rate(currency.upper())
        
        if not rate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exchange rate not found for currency: {currency}"
            )
        
        return SuccessResponse(
            message="Exchange rate retrieved successfully",
            data=ExchangeRateResponse.from_orm(rate)
        )
    except RateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve exchange rate"
        )

@router.get("/all", response_model=SuccessResponse[MultipleRatesResponse])
async def get_all_rates(
    db: Session = Depends(get_db)
):
    """Get current exchange rates for all supported currencies"""
    try:
        rate_service = RateService(db)
        rates = await rate_service.get_all_current_rates()
        
        return SuccessResponse(
            message="All exchange rates retrieved successfully",
            data=MultipleRatesResponse(
                rates=[ExchangeRateResponse.from_orm(rate) for rate in rates],
                last_updated=max(rate.last_updated for rate in rates) if rates else datetime.utcnow()
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve exchange rates"
        )

@router.post("/calculate", response_model=SuccessResponse[RateCalculationResponse])
async def calculate_amount(
    calculation_request: RateCalculationRequest,
    db: Session = Depends(get_db)
):
    """Calculate BDT amount with service fees for foreign currency amount"""
    try:
        rate_service = RateService(db)
        calculation = await rate_service.calculate_bdt_amount(calculation_request)
        
        return SuccessResponse(
            message="Amount calculated successfully",
            data=calculation
        )
    except RateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate amount"
        )

@router.get("/history/{currency_code}", response_model=SuccessResponse[RateHistoryResponse])
async def get_rate_history(
    currency_code: str,
    days: int = Query(7, ge=1, le=365, description="Number of days of history"),
    db: Session = Depends(get_db)
):
    """Get exchange rate history for a specific currency"""
    try:
        rate_service = RateService(db)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        rates = await rate_service.get_rate_history(currency_code.upper(), start_date, end_date)
        
        return SuccessResponse(
            message="Rate history retrieved successfully",
            data=RateHistoryResponse(
                currency_code=currency_code.upper(),
                rates=[ExchangeRateResponse.from_orm(rate) for rate in rates],
                period_start=start_date,
                period_end=end_date
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rate history"
        )

@router.post("/update", response_model=SuccessResponse[BulkRateUpdateResponse])
async def update_rates(
    background_tasks: BackgroundTasks,
    currencies: Optional[List[str]] = Query(None, description="Specific currencies to update"),
    force: bool = Query(False, description="Force update even if rates are fresh"),
    db: Session = Depends(get_db)
):
    """Manually trigger exchange rate updates"""
    try:
        rate_fetcher = RateFetcher(db)
        
        # Add update task to background
        background_tasks.add_task(
            rate_fetcher.update_rates_background,
            currencies or [],
            force
        )
        
        return SuccessResponse(
            message="Rate update initiated successfully",
            data={
                "update_id": f"manual-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "status": "initiated",
                "currencies": currencies or "all"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate rate update"
        )

@router.get("/health", response_model=SuccessResponse)
async def rate_service_health(
    db: Session = Depends(get_db)
):
    """Health check for rate service with data freshness"""
    try:
        rate_service = RateService(db)
        health_info = await rate_service.get_service_health()
        
        return SuccessResponse(
            message="Rate service health check",
            data=health_info
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )

@router.get("/compare", response_model=SuccessResponse)
async def compare_rates(
    base_currency: str = Query("USD", description="Base currency for comparison"),
    target_currencies: List[str] = Query(["EUR", "GBP", "CAD"], description="Currencies to compare"),
    amount: float = Query(1000.0, description="Amount to compare"),
    db: Session = Depends(get_db)
):
    """Compare exchange rates across multiple currencies"""
    try:
        rate_service = RateService(db)
        comparison = await rate_service.compare_currencies(base_currency, target_currencies, amount)
        
        return SuccessResponse(
            message="Currency comparison completed",
            data=comparison
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare currencies"
        )
