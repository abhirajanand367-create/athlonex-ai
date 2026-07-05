import os
import tempfile
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from app.services.pose.detector import PoseDetector
from app.services.analysis.metrics import MetricsComputer
from app.services.detection.object_detector import ObjectDetector
from app.schemas.analysis import (
    VideoAnalysisRequest, VideoAnalysisResponse,
    SportType, ActivityType, PoseFrame,
)

router = APIRouter()
pose_detector = PoseDetector()
metrics_computer = MetricsComputer()
object_detector = ObjectDetector()


def _estimate_fps(video_path: str) -> float:
    import cv2
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    return fps if fps > 0 else 30.0


def _get_duration(video_path: str) -> float:
    import cv2
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return total / fps if fps > 0 else 0


@router.post("/analyze", response_model=VideoAnalysisResponse)
async def analyze_video(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    video_url: Optional[str] = Form(None),
    sport: SportType = Form(...),
    activity_type: Optional[ActivityType] = Form(None),
    athlete_id: Optional[str] = Form(None),
    analyze_pose: bool = Form(True),
    analyze_performance: bool = Form(True),
    detect_objects: bool = Form(False),
    frame_interval: int = Form(30),
):
    if not file and not video_url:
        raise HTTPException(status_code=400, detail="Either file or video_url must be provided")

    video_id = str(uuid.uuid4())
    temp_path = None

    try:
        if file:
            ext = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                content = await file.read()
                tmp.write(content)
                temp_path = tmp.name
        else:
            import httpx
            resp = httpx.get(video_url, follow_redirects=True)
            resp.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(resp.content)
                temp_path = tmp.name

        fps = _estimate_fps(temp_path)
        duration = _get_duration(temp_path)
        total_frames = int(duration * fps)

        response = VideoAnalysisResponse(
            video_id=video_id,
            duration_seconds=duration,
            total_frames=total_frames,
            fps=fps,
        )

        if analyze_pose:
            pose_result, frames = pose_detector.analyze_video(
                temp_path, frame_interval=frame_interval
            )
            response.pose_analysis = pose_result
            response.key_frames = frames[:10]

        if analyze_performance and response.key_frames:
            metrics = metrics_computer.compute_metrics(
                response.key_frames, fps, sport, activity_type
            )
            response.performance_metrics = metrics
            report = metrics_computer.generate_report(metrics, response.pose_analysis, sport, activity_type)
            response.report = report

        if detect_objects:
            detections = object_detector.detect_video(temp_path, frame_interval=frame_interval)
            response.detections = detections

        response.status = "completed"

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            background_tasks.add_task(os.unlink, temp_path)

    return response


@router.post("/analyze-frame")
async def analyze_frame(file: UploadFile = File(...)):
    content = await file.read()
    landmarks = pose_detector.analyze_frame(content)
    if landmarks is None:
        raise HTTPException(status_code=400, detail="No pose detected in image")
    return {"landmarks": landmarks.model_dump()}


@router.get("/supported-sports")
async def get_supported_sports():
    return {
        "sports": [s.value for s in SportType],
        "activities": [a.value for a in ActivityType],
    }
