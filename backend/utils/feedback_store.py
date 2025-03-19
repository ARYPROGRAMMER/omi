import json
from datetime import datetime
from typing import Dict, List

class FeedbackStore:
    def __init__(self, filepath: str = "prompt_feedback.json"):
        self.filepath = filepath
        self.feedback_data = self._load_data()

    def _load_data(self) -> Dict:
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"prompts": {}, "evaluations": []}

    def _save_data(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.feedback_data, f, indent=2)

    def record_prompt_feedback(self, prompt_name: str, score: float):
        if prompt_name not in self.feedback_data["prompts"]:
            self.feedback_data["prompts"][prompt_name] = []
        
        self.feedback_data["prompts"][prompt_name].append({
            "score": score,
            "timestamp": datetime.now().isoformat()
        })
        self._save_data()

    def record_evaluation(self, question: str, response: str, 
                         prompt_name: str, eval_score: float):
        self.feedback_data["evaluations"].append({
            "question": question,
            "response": response,
            "prompt_name": prompt_name,
            "eval_score": eval_score,
            "timestamp": datetime.now().isoformat()
        })
        self._save_data()

    def get_prompt_performance(self) -> Dict[str, float]:
        performance = {}
        for prompt_name, scores in self.feedback_data["prompts"].items():
            if scores:
                performance[prompt_name] = sum(s["score"] for s in scores) / len(scores)
        return performance

    def get_recent_evaluations(self, limit: int = 100) -> List[Dict]:
        return sorted(
            self.feedback_data["evaluations"],
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]
