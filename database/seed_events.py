"""
Seeds the five TECHFINIX '26 events into MongoDB.

Run once after setup_database.py:
    python database/seed_events.py
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database._connection import get_client  # noqa: E402

EVENTS = [
    {
        "slug": "project-expo",
        "name": "Project Expo",
        "category": "technical",
        "order": 1,
        "day": "Day 1 · 10 September 2026",
        "description": "Present an innovative project from any biotechnology theme or domain.",
        "theme_note": "Open theme — any biotechnology domain.",
        "rounds": [],
        "status": "upcoming",
        "image": "/static/images/events/project-expo.jpg",
    },
    {
        "slug": "paper-presentation",
        "name": "Paper Presentation",
        "category": "technical",
        "order": 2,
        "day": "Day 1 · 10 September 2026",
        "description": "Present research, concepts or discoveries from any biotechnology domain.",
        "theme_note": "Open theme — any biotechnology domain.",
        "rounds": [],
        "status": "upcoming",
        "image": "/static/images/events/paper-presentation.jpg",
    },
    {
        "slug": "experiment-detection",
        "name": "Experiment Detection Challenge",
        "category": "non_technical",
        "order": 3,
        "day": "Day 2 · 11 September 2026",
        "description": (
            "An engaging, knowledge-based event testing participants' ability to identify, "
            "understand and interpret laboratory experiments through clues, observations and "
            "results, across Biochemistry, Molecular Biology and Genetic Engineering concepts. "
            "Completed within 2 hours; suitable for Biotechnology, Biochemistry, Microbiology "
            "and other Life Science backgrounds."
        ),
        "duration": "2 hours",
        "rounds": [
            {"title": "Lab Detective", "description": "Identify basic laboratory apparatus, reagents, experiments and their principles."},
            {"title": "Mystery Lab", "description": "Solve experimental clues and identify the experiment based on observations, procedures and results."},
            {"title": "BioLab Escape", "description": "Analyse experimental results, identify errors, and solve a complete experimental mystery using logical and scientific thinking."},
        ],
        "status": "upcoming",
        "image": "/static/images/events/experiment-detection.jpg",
    },
    {
        "slug": "molecule-docking",
        "name": "Molecule Docking Challenge",
        "category": "non_technical",
        "order": 4,
        "day": "Day 2 · 11 September 2026",
        "description": (
            "In this 30-minute hands-on challenge, participants receive only the target protein "
            "structure. They must independently identify suitable ligand molecules, prepare the "
            "target and ligands, and perform molecular docking using PyRx-AutoDock Vina."
        ),
        "duration": "30 minutes",
        "tasks": [
            "Analyze the given target protein",
            "Identify a suitable binding/active site",
            "Select an appropriate ligand from available chemical databases/resources",
            "Prepare the protein and ligand",
            "Perform docking using PyRx",
            "Compare docking scores and binding poses",
            "Identify the best ligand-protein interaction",
            "Submit final docking result and brief interpretation",
        ],
        "rounds": [],
        "status": "upcoming",
        "image": "/static/images/events/molecule-docking.jpg",
    },
    {
        "slug": "biomolecule-puzzle",
        "name": "Biomolecule Puzzle",
        "category": "non_technical",
        "order": 5,
        "day": "Day 2 · 11 September 2026",
        "description": (
            "A three-round scientific quiz testing knowledge of biomolecules, food, and molecular "
            "structures — encouraging quick thinking, teamwork and applied biochemistry."
        ),
        "team_size": "2 members per team",
        "max_teams": 25,
        "rounds": [
            {"title": "Molecular Warmup", "description": "Questions on carbohydrates, proteins, lipids and nucleic acids, plus a hint-based question."},
            {"title": "Molecular Bingo", "description": "Identify or connect clues related to food components and their biological importance."},
            {"title": "Structural Smackdown", "description": "Identify the biomolecule or molecule from given structural clues."},
        ],
        "status": "upcoming",
        "image": "/static/images/events/biomolecule-puzzle.jpg",
    },
]


def run():
    client = get_client()
    db = client[os.environ.get("MONGODB_DB", "techfinix26")]

    for event in EVENTS:
        event["updated_at"] = datetime.now(timezone.utc)
        db.events.update_one({"slug": event["slug"]}, {"$set": event}, upsert=True)
        print(f"  ✓ seeded event: {event['name']}")

    print(f"\nDone. {len(EVENTS)} events seeded into '{db.name}'.")


if __name__ == "__main__":
    run()
