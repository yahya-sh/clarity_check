#!/usr/bin/env python3
"""
Debug script to test the participant join flow
"""
import os
import sys
import json
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.insert(0, '/Users/ysh/Remotecoders/Final_Project/Project')

from repositories.runs import save_run_data, join_participant, get_unexpired_run_by_pin, load_run_data
from services.participant_service import ParticipantService
from utils.session_utils import check_participant_in_run_file, validate_participant_session
from models.participant import Participant

def create_test_run():
    """Create a test run for debugging"""
    print("Creating test run...")
    
    username = "test_instructor"
    presentation_uuid = "test-presentation-uuid"
    session_uuid = "test-session-uuid"
    pin_code = "123456"
    expires_at = datetime.now() + timedelta(hours=1)
    
    # Create test run data
    run_data = save_run_data(
        username=username,
        presentation_uuid=presentation_uuid,
        session_uuid=session_uuid,
        pin_code=pin_code,
        expires_at=expires_at
    )
    
    print(f"Created run: {run_data}")
    return run_data

def test_join_flow():
    """Test the complete join flow"""
    print("\n=== Testing Participant Join Flow ===")
    
    # Create test run
    run_data = create_test_run()
    
    # Test 1: Check if run can be found by PIN
    print("\n1. Testing get_unexpired_run_by_pin...")
    found_run = get_unexpired_run_by_pin("123456")
    print(f"Found run: {found_run is not None}")
    
    # Test 2: Test join participant
    print("\n2. Testing join_participant...")
    if found_run:
        participant = join_participant(found_run, "TestNickname")
        print(f"Created participant: {participant}")
        print(f"Participant UUID: {participant.uuid}")
        
        # Test 3: Check if participant exists in run file
        print("\n3. Testing check_participant_in_run_file...")
        participant_in_run = check_participant_in_run_file(
            "test_instructor",
            "test-presentation-uuid", 
            participant.uuid
        )
        print(f"Participant found in run: {participant_in_run}")
        
        # Test 4: Load run data and check participants
        print("\n4. Testing load_run_data...")
        loaded_run = load_run_data("test_instructor", "test-presentation-uuid")
        if loaded_run:
            print(f"Loaded run participants: {loaded_run.get('participants', [])}")
        
        # Test 5: Test ParticipantService.join_session_run
        print("\n5. Testing ParticipantService.join_session_run...")
        success, error_message, participant_obj, run_obj = ParticipantService.join_session_run("123456", "TestNickname2")
        print(f"Join success: {success}")
        print(f"Error message: {error_message}")
        if participant_obj:
            print(f"Participant UUID: {participant_obj.uuid}")
            
            # Test 6: Check if second participant is in run
            print("\n6. Testing check_participant_in_run_file for second participant...")
            participant2_in_run = check_participant_in_run_file(
                "test_instructor",
                "test-presentation-uuid",
                participant_obj.uuid
            )
            print(f"Second participant found in run: {participant2_in_run}")
            
            # Test 7: Test get_session_for_participant with run data
            print("\n7. Testing get_session_for_participant...")
            success, error_message, session_data = ParticipantService.get_session_for_participant(
                "test_instructor",
                "test-presentation-uuid",
                "test-session-uuid"
            )
            print(f"get_session_for_participant success: {success}")
            print(f"Error message: {error_message}")
            if session_data:
                print(f"Session data status: {session_data.get('status')}")
                print(f"Is run phase: {session_data.get('is_run_phase')}")
                print(f"Participants in session data: {len(session_data.get('participants', []))}")
    else:
        print("ERROR: Could not find run by PIN")

if __name__ == "__main__":
    test_join_flow()
