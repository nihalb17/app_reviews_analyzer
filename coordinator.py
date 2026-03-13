"""
Coordinator Module - Orchestrates Phases 1-5 for the Reviews Analyser
"""
import os
import sys
import json
import datetime
import logging
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.resolve()
HISTORY_FILE = (BASE_DIR / 'backend' / 'backend_data' / 'history.json').resolve()

# Ensure backend_data directory exists
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

# Initialize empty history file if not exists
if not HISTORY_FILE.exists():
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)


def update_history(trigger_id, status, details=None):
    """Update the status of a trigger in history"""
    try:
        if not HISTORY_FILE.exists():
            return
            
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # Find and update the entry
        for entry in history:
            if entry.get('id') == trigger_id:
                entry['status'] = status
                if details:
                    entry.update(details)
                entry['updated_at'] = datetime.datetime.now().isoformat()
                break
        
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4)
            
        logger.info(f"Updated trigger {trigger_id} status to: {status}")
    except Exception as e:
        logger.error(f"Failed to update history: {e}")


def run_full_pipeline(trigger_id, reviews_count, weeks, role, recipient_name, recipient_email, mode="email", resume_from=None):
    """
    Run the full pipeline (Phases 1-5)
    
    Args:
        trigger_id: Unique identifier for this trigger
        reviews_count: Number of reviews to fetch
        weeks: Time period in weeks
        role: Target role (Product, Support, UI/UX, Leadership)
        recipient_name: Name of the recipient
        recipient_email: Email of the recipient
        mode: 'email' or 'preview'
        resume_from: Status to resume from (e.g., 'Data Fetched', 'Themes Created', etc.)
    """
    logger.info(f"Starting pipeline for trigger {trigger_id}")
    logger.info(f"Config: {reviews_count} reviews, {weeks} weeks, role={role}, mode={mode}, resume_from={resume_from}")
    
    # Map status to phase number for resuming
    # If a stage failed, we need to retry that stage
    status_to_phase = {
        None: 1,
        'Started': 1,
        'Data Fetched': 1,  # Data Fetched(Failed) means Phase 1 failed, retry Phase 1
        'Themes Created': 2,  # Themes Created(Failed) means Phase 2 theme extraction failed, retry Phase 2
        'Reviews Classified': 2,  # Reviews Classified(Failed) means Phase 2 classification failed, retry Phase 2
        'Insight Generation': 3,  # Insight Generation(Failed) means Phase 3 failed, retry Phase 3
        'Report Generated': 4,  # Report Generated(Failed) means Phase 4 failed, retry Phase 4
        'Mail Sent': 5,  # Mail Sent(Failed) means Phase 5 failed, retry Phase 5
    }
    start_phase = status_to_phase.get(resume_from, 1)
    logger.info(f"Resuming from phase {start_phase}")
    
    try:
        # Phase 1: Data Ingestion (skip if resuming from later phase)
        if start_phase <= 1:
            update_history(trigger_id, "Started")
        else:
            logger.info(f"Skipping Phase 1 (resuming from phase {start_phase})")
        
        # Add paths for phase imports
        phase1_path = str(BASE_DIR / 'backend' / 'Phase_1_Data_Ingestion_Layer')
        phase2_path = str(BASE_DIR / 'backend' / 'Phase_2_Theme_Extraction_Classification')
        phase3_path = str(BASE_DIR / 'backend' / 'Phase_3_Insight_Generation')
        phase4_path = str(BASE_DIR / 'backend' / 'Phase_4_Report_Generation')
        phase5_path = str(BASE_DIR / 'backend' / 'Phase_5_Email_Service')
        
        # Insert at beginning of path to ensure proper module resolution
        for p in [phase5_path, phase4_path, phase3_path, phase2_path, phase1_path]:
            if p not in sys.path:
                sys.path.insert(0, p)
        
        logger.info(f"Python path updated with phase directories")
        
        # Phase 1: Fetch reviews
        if start_phase <= 1:
            logger.info("Phase 1: Data Ingestion")
            try:
                from app.services.ingestion_service import DataIngestionService
                ingestion_service = DataIngestionService()
                
                period_days = weeks * 7
                result = ingestion_service.ingest_reviews(
                    count=reviews_count,
                    period_days=period_days,
                    save_to_db=True
                )
                
                fetched_count = len(result.get('reviews', []))
                logger.info(f"Fetched {fetched_count} reviews")
                
                # Save filtered reviews to files for Phase 2
                if fetched_count > 0:
                    try:
                        from app.services.storage.file_storage import FileStorageService
                        storage = FileStorageService(data_dir=str(BASE_DIR / 'backend' / 'Phase_1_Data_Ingestion_Layer' / 'data'))
                        storage.save_reviews_json(result['reviews'], filename="groww_reviews.json")
                        storage.save_reviews_csv(result['reviews'], filename="groww_reviews.csv")
                        logger.info(f"Saved {fetched_count} reviews to files")
                    except Exception as save_err:
                        logger.error(f"Failed to save reviews to files: {save_err}")
                
                update_history(trigger_id, "Data Fetched", {'fetched_count': fetched_count})
                
            except Exception as e:
                logger.error(f"Phase 1 failed: {e}")
                update_history(trigger_id, "Data Fetched(Failed)", {'error': str(e)})
                return {'status': 'failed', 'phase': 1, 'error': str(e)}
        else:
            logger.info("Skipping Phase 1 (using existing data)")
        
        # Phase 2: Theme Extraction
        if start_phase <= 2:
            logger.info("Phase 2: Theme Extraction & Classification")
            
            try:
                # Run Phase 2 in a subprocess to avoid import conflicts with Phase 1
                phase2_dir = str(BASE_DIR / 'backend' / 'Phase_2_Theme_Extraction_Classification')
                reviews_file = str(BASE_DIR / 'backend' / 'Phase_1_Data_Ingestion_Layer' / 'data' / 'groww_reviews.json')
                output_file = str(BASE_DIR / 'backend' / 'Phase_2_Theme_Extraction_Classification' / 'data' / f'themes_{role.lower().replace("/", "_")}.json')
                
                # Run the phase 2 script as a subprocess
                result = subprocess.run(
                    [
                        'python', 
                        str(BASE_DIR / 'backend' / 'Phase_2_Theme_Extraction_Classification' / 'run_phase2.py'),
                        '--reviews-file', reviews_file,
                        '--role', role,
                        '--max-themes', '5',
                        '--output-dir', 'data'
                    ],
                    capture_output=True,
                    text=True,
                    cwd=phase2_dir
                )
                
                if result.returncode != 0:
                    raise Exception(f"Phase 2 subprocess failed: {result.stderr}")
                
                # Load the result from the output file
                output_file = str(BASE_DIR / 'backend' / 'Phase_2_Theme_Extraction_Classification' / 'data' / f'themes_{role.lower().replace("/", "_")}.json')
                with open(output_file, 'r', encoding='utf-8') as f:
                    themes_result = json.load(f)
                
                # Check if Phase 2 succeeded or failed
                if themes_result.get('status') == 'failed':
                    # Check if themes were extracted (Themes Created step passed)
                    if themes_result.get('themes') and len(themes_result['themes']) > 0:
                        # Themes were created but classification failed
                        logger.error(f"Classification failed: {themes_result.get('error')}")
                        update_history(trigger_id, "Reviews Classified(Failed)", {'error': themes_result.get('error')})
                    else:
                        # Theme extraction itself failed
                        logger.error(f"Theme extraction failed: {themes_result.get('error')}")
                        update_history(trigger_id, "Themes Created(Failed)", {'error': themes_result.get('error')})
                    return {'status': 'failed', 'phase': 2, 'error': themes_result.get('error')}
                
                logger.info(f"Extracted themes: {themes_result}")
                update_history(trigger_id, "Reviews Classified")
                
            except Exception as e:
                logger.error(f"Phase 2 failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Check if this is before or after theme extraction
                update_history(trigger_id, "Themes Created(Failed)", {'error': str(e)})
                return {'status': 'failed', 'phase': 2, 'error': str(e)}
        else:
            logger.info("Skipping Phase 2 (using existing data)")
        
        # Phase 3: Insight Generation
        if start_phase <= 3:
            logger.info("Phase 3: Insight Generation")
            try:
                # Run Phase 3 in a subprocess to avoid import conflicts
                phase3_dir = str(BASE_DIR / 'backend' / 'Phase_3_Insight_Generation')
                themes_file = str(BASE_DIR / 'backend' / 'Phase_2_Theme_Extraction_Classification' / 'data' / f'themes_{role.lower().replace("/", "_")}.json')
                reviews_file = str(BASE_DIR / 'backend' / 'Phase_1_Data_Ingestion_Layer' / 'data' / 'groww_reviews.json')
                
                result = subprocess.run(
                    [
                        'python',
                        str(BASE_DIR / 'backend' / 'Phase_3_Insight_Generation' / 'run_phase3.py'),
                        '--mode', 'single',
                        '--role', role,
                        '--themes-file', themes_file,
                        '--reviews-file', reviews_file,
                        '--period', f'Last {weeks} weeks'
                    ],
                    capture_output=True,
                    text=True,
                    cwd=phase3_dir
                )
                
                if result.returncode != 0:
                    raise Exception(f"Phase 3 subprocess failed: {result.stderr}")
                
                logger.info(f"Phase 3 completed successfully")
                update_history(trigger_id, "Insight Generation")
                
            except Exception as e:
                logger.error(f"Phase 3 failed: {e}")
                update_history(trigger_id, "Insight Generation(Failed)", {'error': str(e)})
                return {'status': 'failed', 'phase': 3, 'error': str(e)}
        else:
            logger.info("Skipping Phase 3 (using existing data)")
        
        # Phase 4: Report Generation
        if start_phase <= 4:
            logger.info("Phase 4: Report Generation")
            try:
                # Run Phase 4 in a subprocess to avoid import conflicts
                phase4_dir = str(BASE_DIR / 'backend' / 'Phase_4_Report_Generation')
                insights_file = str(BASE_DIR / 'backend' / 'Phase_3_Insight_Generation' / 'data' / f'insights_{role.lower().replace("/", "_")}.json')
                reviews_file = str(BASE_DIR / 'backend' / 'Phase_1_Data_Ingestion_Layer' / 'data' / 'groww_reviews.json')
                safe_role = role.lower().replace('/', '_')
                output_file = str(BASE_DIR / 'backend' / 'Phase_4_Report_Generation' / 'output' / f'groww_insights_{safe_role}.pdf')
                
                result = subprocess.run(
                    [
                        'python',
                        str(BASE_DIR / 'backend' / 'Phase_4_Report_Generation' / 'run_phase4.py'),
                        '--insights-file', insights_file,
                        '--reviews-file', reviews_file,
                        '--role', role,
                        '--output-dir', 'output'
                    ],
                    capture_output=True,
                    text=True,
                    cwd=phase4_dir
                )
                
                if result.returncode != 0:
                    raise Exception(f"Phase 4 subprocess failed: {result.stderr}")
                
                logger.info(f"Phase 4 completed successfully")
                update_history(trigger_id, "Report Generated", {'pdf_path': output_file})
                
            except Exception as e:
                logger.error(f"Phase 4 failed: {e}")
                update_history(trigger_id, "Report Generated(Failed)", {'error': str(e)})
                return {'status': 'failed', 'phase': 4, 'error': str(e)}
        else:
            logger.info("Skipping Phase 4 (using existing data)")
        
        # Phase 5: Email Service (only if mode is 'email')
        if mode == "email":
            if start_phase <= 5:
                logger.info("Phase 5: Email Service")
                try:
                    # Run Phase 5 in a subprocess to avoid import conflicts
                    phase5_dir = str(BASE_DIR / 'backend' / 'Phase_5_Email_Service')
                    safe_role = role.lower().replace('/', '_')
                    pdf_path = str(BASE_DIR / 'backend' / 'Phase_4_Report_Generation' / 'output' / f'groww_insights_{safe_role}.pdf')
                    html_path = str(BASE_DIR / 'backend' / 'Phase_4_Report_Generation' / 'output' / f'groww_insights_{safe_role}.html')
                    
                    result = subprocess.run(
                        [
                            'python',
                            str(BASE_DIR / 'backend' / 'Phase_5_Email_Service' / 'send_email.py'),
                            '--role', role,
                            '--recipient', recipient_email,
                            '--html-file', html_path,
                            '--pdf-file', pdf_path,
                            '--subject', f'Groww Playstore Reviews Insights - {role} Team'
                        ],
                        capture_output=True,
                        text=True,
                        cwd=phase5_dir
                    )
                    
                    if result.returncode != 0:
                        raise Exception(f"Phase 5 subprocess failed: {result.stderr}")
                    
                    logger.info(f"Phase 5 completed successfully")
                    update_history(trigger_id, "Mail Sent")
                    
                except Exception as e:
                    logger.error(f"Phase 5 failed: {e}")
                    update_history(trigger_id, "Mail Sent(Failed)", {'error': str(e)})
                    return {'status': 'failed', 'phase': 5, 'error': str(e)}
            else:
                logger.info("Skipping Phase 5 (using existing data)")
        else:
            logger.info("Skipping Phase 5 (Preview Mode)")
            if start_phase <= 4:
                update_history(trigger_id, "Report Generated")
        
        logger.info(f"Pipeline completed successfully for trigger {trigger_id}")
        return {'status': 'success', 'trigger_id': trigger_id}
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        update_history(trigger_id, "Started(Failed)", {'error': str(e)})
        return {'status': 'failed', 'error': str(e)}


if __name__ == '__main__':
    # Test the pipeline
    import uuid
    test_id = str(uuid.uuid4())
    result = run_full_pipeline(
        trigger_id=test_id,
        reviews_count=100,
        weeks=2,
        role="Product",
        recipient_name="Test User",
        recipient_email="test@example.com",
        mode="preview"
    )
    print(f"Result: {result}")
