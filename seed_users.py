import os
import random
import uuid
import math
from datetime import datetime, timedelta, timezone

from app import app, db
from models import User, ApiKey, EncodeJob
import bcrypt

def get_random_date_exponential(start_date, end_date):
    """
    Generate a random date biased towards the end_date to simulate growth.
    """
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    
    # Generate random number with exponential distribution (more towards the end)
    # math.pow(random.random(), 2) will skew the uniform distribution [0,1) towards 0
    # We want to skew towards the end, so we do 1 - pow(random, 2) to skew towards 1
    # Actually, random.random() ** 0.5 skews towards 1
    random_days = int((random.random() ** 0.5) * days_between_dates)
    
    return start_date + timedelta(days=random_days)

def main():
    with app.app_context():
        print("Clearing existing synthetic data...")
        db.session.query(EncodeJob).filter_by(is_synthetic=True).delete()
        db.session.query(ApiKey).filter_by(is_synthetic=True).delete()
        db.session.query(User).filter_by(is_synthetic=True).delete()
        db.session.commit()

        NUM_USERS = 10000
        NUM_JOBS = 50000
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=365)
        
        print(f"Generating {NUM_USERS} synthetic users...")
        
        # Batch insert users
        users = []
        for i in range(NUM_USERS):
            created_at = get_random_date_exponential(start_date, end_date)
            # Use a dummy hash to save time since it's synthetic data
            dummy_hash = f"$2b$12$dummyhash{i}".ljust(60, 'x')
            user = User(
                email=f"synthetic_user_{i}@example.com",
                password_hash=dummy_hash,
                created_at=created_at,
                updated_at=created_at,
                is_synthetic=True
            )
            users.append(user)
            
            if len(users) >= 1000:
                db.session.bulk_save_objects(users)
                db.session.commit()
                users = []
                
        if users:
            db.session.bulk_save_objects(users)
            db.session.commit()
            
        print("Fetching user IDs...")
        all_user_ids = [u.id for u in db.session.query(User.id).filter_by(is_synthetic=True).all()]
        
        print(f"Generating API Keys for some users...")
        api_keys = []
        # Not all users have API keys, maybe 30% of them
        key_users = random.sample(all_user_ids, int(NUM_USERS * 0.3))
        for uid in key_users:
            key_hash = str(uuid.uuid4())
            api_keys.append(ApiKey(
                user_id=uid,
                key_hash=key_hash,
                key_prefix=key_hash[:8],
                label="Synthetic Key",
                is_synthetic=True,
                created_at=get_random_date_exponential(start_date, end_date)
            ))
        db.session.bulk_save_objects(api_keys)
        db.session.commit()

        print(f"Generating {NUM_JOBS} synthetic encode jobs...")
        jobs = []
        # Power-law distribution for user activity
        # We will create a pool of user IDs where some appear much more frequently
        # To do this efficiently, we can use random.choices with weights, or just pick from a predefined skewed list.
        # Let's assign a 'weight' to each user: 1 / (rank ^ 0.8)
        # To keep it fast, we'll just use a Pareto distribution to pick user indices.
        
        for i in range(NUM_JOBS):
            # Pareto distribution returns values >= 1. We scale and map it to an index.
            # a=1.16 gives the 80-20 rule roughly.
            pareto_val = random.paretovariate(1.16)
            # Normalize to our user count (roughly)
            # This is a bit ad-hoc, but works for simulation.
            # We want an integer between 0 and NUM_USERS-1.
            # Since pareto can be very large, we use modulo.
            user_idx = int(pareto_val * 100) % NUM_USERS
            uid = all_user_ids[user_idx]
            
            job_date = get_random_date_exponential(start_date, end_date)
            
            jobs.append(EncodeJob(
                user_id=uid,
                file_hash=str(uuid.uuid4()),
                huffman_dict={"dummy": "data"},
                created_at=job_date,
                is_synthetic=True
            ))
            
            if len(jobs) >= 2000:
                db.session.bulk_save_objects(jobs)
                db.session.commit()
                jobs = []
                
        if jobs:
            db.session.bulk_save_objects(jobs)
            db.session.commit()
            
        print("Database seeded with synthetic data successfully!")

if __name__ == "__main__":
    main()
