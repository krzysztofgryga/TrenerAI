from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.agent import app_graph

app = FastAPI(title="Trainer AI API", description="Backend dla aplikacji trenerskiej")


# Model wejściowy (Request)
class TrainingRequest(BaseModel):
    num_people: int
    difficulty: str  # easy, medium, hard
    rest_time: int
    mode: str  # circuit, common


@app.get("/")
def read_root():
    return {"status": "AI Trainer System Online 🚀"}


@app.post("/generate-training")
async def generate_training(request: TrainingRequest):
    """
    Endpoint generujący pełny plan treningowy przy użyciu LangGraph.
    """
    try:
        inputs = {
            "num_people": request.num_people,
            "difficulty": request.difficulty,
            "rest_time": request.rest_time,
            "mode": request.mode
        }

        # Uruchomienie agenta
        result = app_graph.invoke(inputs)

        return result["final_plan"]

    except Exception as e:
        print(f"Błąd: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)