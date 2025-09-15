"""Politicians API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...database import get_db
from ...database.models import Politician
from ...social_media import SocialMediaAnalyzer
from ..schemas import PoliticianResponse, PoliticianCreate, SocialMediaAccountRequest

router = APIRouter()


@router.get("/", response_model=List[PoliticianResponse])
async def get_politicians(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    party: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of politicians with optional filtering."""
    query = db.query(Politician)
    
    if party:
        query = query.filter(Politician.party == party)
    
    if state:
        query = query.filter(Politician.state == state)
    
    politicians = query.offset(skip).limit(limit).all()
    return politicians


@router.get("/{politician_id}", response_model=PoliticianResponse)
async def get_politician(politician_id: int, db: Session = Depends(get_db)):
    """Get a specific politician by ID."""
    politician = db.query(Politician).filter(Politician.id == politician_id).first()
    
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")
    
    return politician


@router.post("/", response_model=PoliticianResponse)
async def create_politician(
    politician_data: PoliticianCreate,
    db: Session = Depends(get_db)
):
    """Create a new politician record."""
    try:
        politician = Politician(**politician_data.dict())
        db.add(politician)
        db.commit()
        db.refresh(politician)
        return politician
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{politician_id}/social-media")
async def get_politician_social_media(politician_id: int, db: Session = Depends(get_db)):
    """Get social media analysis for a politician."""
    politician = db.query(Politician).filter(Politician.id == politician_id).first()
    
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")
    
    try:
        analyzer = SocialMediaAnalyzer(db)
        analysis = analyzer.analyze_politician_social_media(politician)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{politician_id}/social-media")
async def add_social_media_account(
    politician_id: int,
    account_request: SocialMediaAccountRequest,
    db: Session = Depends(get_db)
):
    """Add a social media account for a politician."""
    politician = db.query(Politician).filter(Politician.id == politician_id).first()
    
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")
    
    try:
        analyzer = SocialMediaAnalyzer(db)
        account = analyzer.create_social_media_account(
            politician=politician,
            platform=account_request.platform,
            username=account_request.username
        )
        
        if not account:
            raise HTTPException(status_code=400, detail="Failed to create social media account")
        
        return {
            "id": account.id,
            "politician_id": account.politician_id,
            "platform": account.platform,
            "username": account.username,
            "followers_count": account.followers_count,
            "verified": account.verified
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{politician_id}/reports")
async def get_politician_reports(politician_id: int, db: Session = Depends(get_db)):
    """Get all reports for a politician."""
    politician = db.query(Politician).filter(Politician.id == politician_id).first()
    
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")
    
    return [
        {
            "id": report.id,
            "report_type": report.report_type,
            "title": report.title,
            "generated_date": report.generated_date,
            "version": report.version
        }
        for report in politician.reports
    ]


@router.get("/{politician_id}/entities")
async def get_politician_entities(politician_id: int, db: Session = Depends(get_db)):
    """Get entities associated with a politician."""
    politician = db.query(Politician).filter(Politician.id == politician_id).first()
    
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")
    
    return [
        {
            "entity_id": pol_entity.entity.id,
            "entity_name": pol_entity.entity.name,
            "entity_type": pol_entity.entity.entity_type,
            "association_type": pol_entity.association_type,
            "strength": pol_entity.strength
        }
        for pol_entity in politician.entity_mentions
    ]