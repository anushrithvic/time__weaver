"""
Module: Timetable Generation & Scheduling (Module 3)
Repository: timeweaver_backend
Owner: Pranathi Nibhanipudi
Epic: 3 - Timetable Generation / Re-generation

Genetic Algorithm Timetable Generator

Simple GA implementation for timetable generation:
- Random population initialization
- Fitness-based tournament selection
- Single-point crossover
- Random mutation
- Elitism (keep best solutions)

Dependencies:
    - app.models.timetable (Timetable, TimetableSlot)
    - app.services.timetable_generator_base (TimetableGeneratorBase)
    - app.services.curriculum_service (CurriculumService)

User Stories: 3.3.2 (Multi-Solution Generation)
"""

import random
import copy
from typing import List
from sqlalchemy.orm import Session

from app.models.timetable import Timetable, TimetableSlot
from app.services.timetable_generator_base import TimetableGeneratorBase
from app.services.curriculum_service import CurriculumService


class GeneticAlgorithmGenerator(TimetableGeneratorBase):
    """Genetic Algorithm for timetable generation"""
    
    def __init__(
        self,
        db: Session,
        population_size: int = 20,
        max_generations: int = 50,
        mutation_rate: float = 0.1,
        elitism_count: int = 2
    ):
        super().__init__(db)
        self.population_size = population_size
        self.max_generations = max_generations
        self.mutation_rate = mutation_rate
        self.elitism_count = elitism_count
    
    def generate(
        self,
        semester_id: int,
        num_solutions: int = 5
    ) -> List[Timetable]:
        """
        Generate multiple timetable solutions using GA.
        
        Args:
            semester_id: Semester to generate for
            num_solutions: Number of solutions to return
            
        Returns:
            List of Timetable objects (best solutions)
        """
        # Get resources
        resources = self.get_all_resources(semester_id)
        
        # Initialize population with random timetables
        population = self._initialize_population(semester_id, resources)
        
        # Evolve population
        for generation in range(self.max_generations):
            # Evaluate fitness
            fitnesses = [self.calculate_fitness(t.id) for t in population]
            
            # Select parents
            parents = self._selection(population, fitnesses)
            
            # Create offspring
            offspring = self._crossover(parents, semester_id)
            
            # Mutate
            offspring = self._mutate(offspring, resources)
            
            # Elitism: keep best solutions
            population_with_fitness = list(zip(population, fitnesses))
            population_with_fitness.sort(key=lambda x: x[1], reverse=True)
            elite = [t for t, f in population_with_fitness[:self.elitism_count]]
            
            # New population = elite + offspring
            population = elite + offspring[:self.population_size - self.elitism_count]
        
        # Update metrics for all timetables
        for timetable in population:
            self.update_timetable_metrics(timetable)
        
        # Return top N solutions
        ranked = self.rank_solutions(population)
        return ranked[:num_solutions]
    
    def _initialize_population(
        self,
        semester_id: int,
        resources: dict
    ) -> List[Timetable]:
        """Create initial random population."""
        population = []
        
        for i in range(self.population_size):
            # Create empty timetable
            timetable = self.initialize_empty_timetable(
                semester_id,
                f"GA Solution {i+1}",
                "GA"
            )
            
            # Generate random schedule
            self._generate_random_schedule(timetable, resources)
            
            population.append(timetable)
        
        return population
    
    def _generate_random_schedule(
        self,
        timetable: Timetable,
        resources: dict
    ):
        """Generate a completely random schedule."""
        sections = resources["sections"]
        rooms = resources["rooms"]
        time_slots = resources["time_slots"]
        days = resources["days"]
        semester = resources["semester"]
        
        for section in sections:
            # Get courses for this section
            courses_data = CurriculumService.get_all_courses_for_section(
                self.db, section, semester
            )
            
            all_courses = (
                courses_data.get("core", []) +
                courses_data.get("electives", []) +
                courses_data.get("projects", [])
            )
            
            # Assign random slots for each course
            for course in all_courses:
                # Random room, time, day
                room = random.choice(rooms)
                time_slot = random.choice(time_slots)
                day = random.choice(days)
                
                # Create slot
                try:
                    self.create_slot_assignment(
                        timetable_id=timetable.id,
                        section_id=section.id,
                        course_id=course.id,
                        room_id=room.id,
                        start_slot_id=time_slot.id,
                        day_of_week=day,
                        duration_slots=1
                    )
                except Exception:
                    continue  # Skip on error
        
        self.db.commit()
    
    def _selection(
        self,
        population: List[Timetable],
        fitnesses: List[float]
    ) -> List[Timetable]:
        """Tournament selection."""
        parents = []
        
        for _ in range(len(population)):
            # Tournament of size 3
            tournament_indices = random.sample(range(len(population)), min(3, len(population)))
            tournament_fitnesses = [fitnesses[i] for i in tournament_indices]
            
            # Select best from tournament
            winner_idx = tournament_indices[tournament_fitnesses.index(max(tournament_fitnesses))]
            parents.append(population[winner_idx])
        
        return parents
    
    def _crossover(
        self,
        parents: List[Timetable],
        semester_id: int
    ) -> List[Timetable]:
        """Single-point crossover to create offspring."""
        offspring = []
        
        for i in range(0, len(parents) - 1, 2):
            parent1 = parents[i]
            parent2 = parents[i + 1]
            
            # Create two children
            child1 = self.initialize_empty_timetable(
                semester_id,
                f"Offspring {i}",
                "GA"
            )
            child2 = self.initialize_empty_timetable(
                semester_id,
                f"Offspring {i+1}",
                "GA"
            )
            
            # Get parent slots
            parent1_slots = self.db.query(TimetableSlot).filter(
                TimetableSlot.timetable_id == parent1.id
            ).all()
            
            parent2_slots = self.db.query(TimetableSlot).filter(
                TimetableSlot.timetable_id == parent2.id
            ).all()
            
            # Crossover point
            if parent1_slots:
                crossover_point = len(parent1_slots) // 2
                
                # Child 1: first half from parent1, second half from parent2
                for slot in parent1_slots[:crossover_point]:
                    self._copy_slot(slot, child1.id)
                
                for slot in parent2_slots[crossover_point:]:
                    self._copy_slot(slot, child1.id)
                
                # Child 2: opposite
                for slot in parent2_slots[:crossover_point]:
                    self._copy_slot(slot, child2.id)
                
                for slot in parent1_slots[crossover_point:]:
                    self._copy_slot(slot, child2.id)
            
            offspring.extend([child1, child2])
        
        self.db.commit()
        return offspring
    
    def _mutate(
        self,
        offspring: List[Timetable],
        resources: dict
    ) -> List[Timetable]:
        """Random mutation: reassign random slots."""
        rooms = resources["rooms"]
        time_slots = resources["time_slots"]
        days = resources["days"]
        
        for timetable in offspring:
            if random.random() < self.mutation_rate:
                # Get all slots
                slots = self.db.query(TimetableSlot).filter(
                    TimetableSlot.timetable_id == timetable.id
                ).all()
                
                if slots:
                    # Mutate a random slot
                    slot_to_mutate = random.choice(slots)
                    
                    # Random changes
                    slot_to_mutate.room_id = random.choice(rooms).id
                    slot_to_mutate.start_slot_id = random.choice(time_slots).id
                    slot_to_mutate.day_of_week = random.choice(days)
        
        self.db.commit()
        return offspring
    
    def _copy_slot(self, slot: TimetableSlot, new_timetable_id: int):
        """Copy a slot to a new timetable."""
        new_slot = TimetableSlot(
            timetable_id=new_timetable_id,
            section_id=slot.section_id,
            course_id=slot.course_id,
            room_id=slot.room_id,
            start_slot_id=slot.start_slot_id,
            duration_slots=slot.duration_slots,
            day_of_week=slot.day_of_week,
            primary_faculty_id=slot.primary_faculty_id,
            batch_number=slot.batch_number,
            is_locked=False
        )
        self.db.add(new_slot)
