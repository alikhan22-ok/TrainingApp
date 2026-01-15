import uuid
import json
import os
from typing import Dict, List, Optional

class Set:
    def __init__(self, weight: float, reps: int, set_id: str = None):
        self.set_id = set_id if set_id else str(uuid.uuid4())
        self.weight = weight
        self.reps = reps

    def to_dict(self):
        return {
            'id': self.set_id,
            'weight': self.weight,
            'reps': self.reps
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(weight=data['weight'], reps=data['reps'], set_id=data['id'])

class Exercise:
    def __init__(self, name: str, rep_min: int, rep_max: int, exercise_id: str = None):
        self.exercise_id = exercise_id if exercise_id else str(uuid.uuid4())
        self.name = name
        self.rep_min = rep_min
        self.rep_max = rep_max
        self.sets: List[Set] = []

    def update_rep_range(self, rep_min: int, rep_max: int):
        self.rep_min = rep_min
        self.rep_max = rep_max

    def add_set(self, weight: float, reps: int) -> str:
        if weight < 0 or reps < 0:
            raise ValueError("Weight and reps must be non-negative.")
        new_set = Set(weight=weight, reps=reps)
        self.sets.append(new_set)
        return new_set.set_id

    def edit_set(self, set_id: str, weight: float, reps: int) -> None:
        if weight < 0 or reps < 0:
            raise ValueError("Weight and reps must be non-negative.")
        for s in self.sets:
            if s.set_id == set_id:
                s.weight = weight
                s.reps = reps
                return
        raise KeyError('Set not found')

    def remove_set(self, set_id: str) -> None:
        for i, s in enumerate(self.sets):
            if s.set_id == set_id:
                del self.sets[i]
                return
        raise KeyError('Set not found')

    def list_sets(self) -> List[dict]:
        return [s.to_dict() for s in self.sets]

    def get_last_set(self):
        if self.sets:
            return self.sets[-1]
        return None

    def to_dict(self) -> dict:
        return {
            'id': self.exercise_id,
            'name': self.name,
            'rep_min': self.rep_min,
            'rep_max': self.rep_max,
            'sets': self.list_sets()
        }

    @classmethod
    def from_dict(cls, data):
        ex = cls(name=data['name'], rep_min=data['rep_min'], rep_max=data['rep_max'], exercise_id=data['id'])
        if 'sets' in data:
            ex.sets = [Set.from_dict(s) for s in data['sets']]
        return ex

class Program:
    def __init__(self, name: str, program_id: str = None):
        self.program_id = program_id if program_id else str(uuid.uuid4())
        self.name = name
        self.exercises: Dict[str, Exercise] = {}

    def to_dict(self) -> dict:
        return {
            'id': self.program_id,
            'name': self.name,
            'exercises': [ex.to_dict() for ex in self.exercises.values()]
        }

    @classmethod
    def from_dict(cls, data):
        prog = cls(name=data['name'], program_id=data['id'])
        if 'exercises' in data:
            for ex_data in data['exercises']:
                ex = Exercise.from_dict(ex_data)
                prog.exercises[ex.exercise_id] = ex
        return prog

class Training:
    def __init__(self, data_file: str = 'workout_data.json'):
        self.programs: Dict[str, Program] = {}
        self.data_file = data_file
        self._load_data()

    def _save_data(self):
        data = [p.to_dict() for p in self.programs.values()]
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving data: {e}")

    def _load_data(self):
        if not os.path.exists(self.data_file):
            return
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                for p_data in data:
                    prog = Program.from_dict(p_data)
                    self.programs[prog.program_id] = prog
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading data: {e}")

    def create_program(self, name: str) -> str:
        program = Program(name=name)
        self.programs[program.program_id] = program
        self._save_data()
        return program.program_id

    def rename_program(self, program_id: str, new_name: str) -> None:
        program = self._get_program_obj(program_id)
        program.name = new_name
        self._save_data()

    def delete_program(self, program_id: str) -> None:
        if program_id in self.programs:
            del self.programs[program_id]
            self._save_data()
        else:
            raise KeyError('Program not found')

    def list_programs(self) -> list:
        return [{'id': pid, 'name': p.name} for pid, p in self.programs.items()]

    def get_program(self, program_id: str) -> dict:
        return self._get_program_obj(program_id).to_dict()

    def add_exercise(self, program_id: str, exercise_name: str, rep_min: int, rep_max: int) -> str:
        program = self._get_program_obj(program_id)
        exercise = Exercise(exercise_name, rep_min, rep_max)
        program.exercises[exercise.exercise_id] = exercise
        self._save_data()
        return exercise.exercise_id

    def rename_exercise(self, program_id: str, exercise_id: str, new_name: str) -> None:
        exercise = self._get_exercise_obj(program_id, exercise_id)
        exercise.name = new_name
        self._save_data()

    def set_exercise_rep_range(self, program_id: str, exercise_id: str, rep_min: int, rep_max: int) -> None:
        exercise = self._get_exercise_obj(program_id, exercise_id)
        exercise.update_rep_range(rep_min, rep_max)
        self._save_data()

    def remove_exercise(self, program_id: str, exercise_id: str) -> None:
        program = self._get_program_obj(program_id)
        if exercise_id in program.exercises:
            del program.exercises[exercise_id]
            self._save_data()
        else:
            raise KeyError('Exercise not found')

    def list_exercises(self, program_id: str) -> list:
        program = self._get_program_obj(program_id)
        return [ex.to_dict() for ex in program.exercises.values()]

    def add_set(self, program_id: str, exercise_id: str, weight: float, reps: int) -> str:
        exercise = self._get_exercise_obj(program_id, exercise_id)
        set_id = exercise.add_set(weight, reps)
        if reps >= exercise.rep_max:
            pass 
        self._save_data()
        return set_id

    def edit_set(self, program_id: str, exercise_id: str, set_id: str, weight: float, reps: int) -> None:
        exercise = self._get_exercise_obj(program_id, exercise_id)
        exercise.edit_set(set_id, weight, reps)
        self._save_data()

    def remove_set(self, program_id: str, exercise_id: str, set_id: str) -> None:
        exercise = self._get_exercise_obj(program_id, exercise_id)
        exercise.remove_set(set_id)
        self._save_data()

    def list_sets(self, program_id: str, exercise_id: str) -> list:
        exercise = self._get_exercise_obj(program_id, exercise_id)
        return exercise.list_sets()

    def get_suggested_weight(self, program_id: str, exercise_id: str) -> float:
        exercise = self._get_exercise_obj(program_id, exercise_id)
        last_set = exercise.get_last_set()
        if last_set is None:
            return 0.0
        if last_set.reps >= exercise.rep_max:
            return last_set.weight + 5.0
        else:
            return last_set.weight

    def _get_program_obj(self, program_id: str) -> Program:
        if program_id not in self.programs:
            raise KeyError('Program not found')
        return self.programs[program_id]

    def _get_exercise_obj(self, program_id: str, exercise_id: str) -> Exercise:
        program = self._get_program_obj(program_id)
        if exercise_id not in program.exercises:
            raise KeyError('Exercise not found')
        return program.exercises[exercise_id]