from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.services.template_service import TemplateService
from app.schemas.template import (
    TemplateCreate, TemplateUpdate, TemplateResponse,
    TemplateRender, TemplateRenderResponse
)
from app.utils.response import SuccessResponse
from app.utils.auth import get_current_service

router = APIRouter()

@router.get("/", response_model=SuccessResponse[List[TemplateResponse]])
async def list_templates(
    channel: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """List notification templates with optional filtering"""
    try:
        template_service = TemplateService(db)
        templates = await template_service.list_templates(
            channel=channel,
            category=category,
            is_active=is_active
        )
        
        return SuccessResponse(
            message="Templates retrieved successfully",
            data=[TemplateResponse.from_orm(t) for t in templates]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve templates"
        )

@router.get("/{template_key}", response_model=SuccessResponse[TemplateResponse])
async def get_template(
    template_key: str,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Get specific notification template"""
    try:
        template_service = TemplateService(db)
        template = await template_service.get_template(template_key)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return SuccessResponse(
            message="Template retrieved successfully",
            data=TemplateResponse.from_orm(template)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve template"
        )

@router.post("/", response_model=SuccessResponse[TemplateResponse])
async def create_template(
    template_data: TemplateCreate,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Create new notification template"""
    try:
        template_service = TemplateService(db)
        template = await template_service.create_template(template_data)
        
        return SuccessResponse(
            message="Template created successfully",
            data=TemplateResponse.from_orm(template)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template"
        )

@router.put("/{template_key}", response_model=SuccessResponse[TemplateResponse])
async def update_template(
    template_key: str,
    template_update: TemplateUpdate,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Update notification template"""
    try:
        template_service = TemplateService(db)
        template = await template_service.update_template(template_key, template_update)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return SuccessResponse(
            message="Template updated successfully",
            data=TemplateResponse.from_orm(template)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update template"
        )

@router.delete("/{template_key}", response_model=SuccessResponse)
async def delete_template(
    template_key: str,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Delete notification template"""
    try:
        template_service = TemplateService(db)
        deleted = await template_service.delete_template(template_key)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return SuccessResponse(
            message="Template deleted successfully",
            data=None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template"
        )

@router.post("/render", response_model=SuccessResponse[TemplateRenderResponse])
async def render_template(
    render_data: TemplateRender,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Render template with provided data"""
    try:
        template_service = TemplateService(db)
        rendered = await template_service.render_template(
            render_data.template_key,
            render_data.template_data
        )
        
        return SuccessResponse(
            message="Template rendered successfully",
            data=rendered
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to render template"
        )
