from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import jinja2
import logging

from app.models.template import NotificationTemplate
from app.schemas.template import (
    TemplateCreate, TemplateUpdate, TemplateRenderResponse
)

logger = logging.getLogger(__name__)

class TemplateService:
    def __init__(self, db: Session):
        self.db = db
        self.jinja_env = jinja2.Environment(
            loader=jinja2.BaseLoader(),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
    
    async def list_templates(
        self,
        channel: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[NotificationTemplate]:
        """List notification templates with filtering"""
        query = self.db.query(NotificationTemplate)
        
        if channel:
            query = query.filter(NotificationTemplate.channel == channel)
        
        if category:
            query = query.filter(NotificationTemplate.category == category)
        
        if is_active is not None:
            query = query.filter(NotificationTemplate.is_active == is_active)
        
        return query.order_by(NotificationTemplate.template_name).all()
    
    async def get_template(self, template_key: str) -> Optional[NotificationTemplate]:
        """Get template by key"""
        return self.db.query(NotificationTemplate).filter(
            NotificationTemplate.template_key == template_key
        ).first()
    
    async def create_template(self, template_data: TemplateCreate) -> NotificationTemplate:
        """Create new notification template"""
        # Check if template key already exists
        existing = await self.get_template(template_data.template_key)
        if existing:
            raise ValueError(f"Template with key '{template_data.template_key}' already exists")
        
        template = NotificationTemplate(
            template_key=template_data.template_key,
            template_name=template_data.template_name,
            description=template_data.description,
            channel=template_data.channel,
            subject_template=template_data.subject_template,
            body_template=template_data.body_template,
            required_variables=template_data.required_variables,
            optional_variables=template_data.optional_variables,
            category=template_data.category
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"Created template: {template_data.template_key}")
        return template
    
    async def update_template(
        self, 
        template_key: str, 
        template_update: TemplateUpdate
    ) -> Optional[NotificationTemplate]:
        """Update notification template"""
        template = await self.get_template(template_key)
        if not template:
            return None
        
        update_data = template_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(template, field, value)
        
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"Updated template: {template_key}")
        return template
    
    async def delete_template(self, template_key: str) -> bool:
        """Delete notification template"""
        template = await self.get_template(template_key)
        if not template:
            return False
        
        self.db.delete(template)
        self.db.commit()
        
        logger.info(f"Deleted template: {template_key}")
        return True
    
    async def render_template(
        self, 
        template_key: str, 
        template_data: Dict[str, Any]
    ) -> TemplateRenderResponse:
        """Render template with provided data"""
        template = await self.get_template(template_key)
        if not template:
            raise ValueError(f"Template '{template_key}' not found")
        
        if not template.is_active:
            raise ValueError(f"Template '{template_key}' is not active")
        
        # Check for missing required variables
        missing_variables = []
        if template.required_variables:
            for var in template.required_variables:
                if var not in template_data:
                    missing_variables.append(var)
        
        try:
            # Render subject (if applicable)
            rendered_subject = None
            if template.subject_template:
                subject_template = self.jinja_env.from_string(template.subject_template)
                rendered_subject = subject_template.render(**template_data)
            
            # Render body
            body_template = self.jinja_env.from_string(template.body_template)
            rendered_body = body_template.render(**template_data)
            
            return TemplateRenderResponse(
                template_key=template_key,
                channel=template.channel,
                rendered_subject=rendered_subject,
                rendered_body=rendered_body,
                missing_variables=missing_variables
            )
            
        except jinja2.TemplateError as e:
            logger.error(f"Template rendering error for {template_key}: {e}")
            raise ValueError(f"Template rendering failed: {str(e)}")
    
    async def validate_template_syntax(self, template_content: str) -> Dict[str, Any]:
        """Validate Jinja2 template syntax"""
        try:
            self.jinja_env.from_string(template_content)
            return {
                "valid": True,
                "error": None
            }
        except jinja2.TemplateError as e:
            return {
                "valid": False,
                "error": str(e)
            }
