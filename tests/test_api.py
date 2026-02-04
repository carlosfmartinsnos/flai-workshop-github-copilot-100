"""
Test cases for the Mergington High School Activities API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    global activities
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_returns_correct_structure(self, client):
        """Test that activity structure is correct"""
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_returns_participants(self, client):
        """Test that participants are included in the response"""
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_valid_activity(self, client):
        """Test successful signup for an existing activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=alice@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up alice@mergington.edu for Chess Club" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "alice@mergington.edu" in activities_data["Chess Club"]["participants"]

    def test_signup_for_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=alice@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_duplicate_participant(self, client):
        """Test that duplicate signups are rejected"""
        # First signup should succeed
        response1 = client.post(
            "/activities/Chess%20Club/signup?email=alice@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            "/activities/Chess%20Club/signup?email=alice@mergington.edu"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert data["detail"] == "Student already signed up for this activity"

    def test_signup_increases_participant_count(self, client):
        """Test that signup increases the participant count"""
        # Get initial count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Programming Class"]["participants"])
        
        # Sign up a new participant
        client.post(
            "/activities/Programming%20Class/signup?email=bob@mergington.edu"
        )
        
        # Verify count increased
        final_response = client.get("/activities")
        final_count = len(final_response.json()["Programming Class"]["participants"])
        assert final_count == initial_count + 1


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant(self, client):
        """Test successful unregistration of an existing participant"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered michael@mergington.edu from Chess Club" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]

    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregister from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_unregister_nonexistent_participant(self, client):
        """Test unregister a participant who isn't signed up"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student is not signed up for this activity"

    def test_unregister_decreases_participant_count(self, client):
        """Test that unregister decreases the participant count"""
        # Get initial count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Chess Club"]["participants"])
        
        # Unregister a participant
        client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        
        # Verify count decreased
        final_response = client.get("/activities")
        final_count = len(final_response.json()["Chess Club"]["participants"])
        assert final_count == initial_count - 1

    def test_signup_after_unregister(self, client):
        """Test that a participant can re-register after unregistering"""
        # Unregister
        client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        
        # Re-register
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant is back
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" in activities_data["Chess Club"]["participants"]
