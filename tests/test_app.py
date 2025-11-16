"""
Tests for the Mergington High School Activities API
"""
from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app)


class TestActivitiesEndpoints:
    """Test suite for the /activities endpoint"""

    def test_get_activities(self):
        """Test fetching all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data


class TestSignupEndpoint:
    """Test suite for the signup endpoint"""

    def setup_method(self):
        """Reset activities before each test"""
        # Store original participants
        self.original_participants = {}
        for activity_name, activity_data in activities.items():
            self.original_participants[activity_name] = activity_data["participants"].copy()

    def teardown_method(self):
        """Restore original participants after each test"""
        for activity_name, original_list in self.original_participants.items():
            activities[activity_name]["participants"] = original_list.copy()

    def test_signup_success(self):
        """Test successful signup"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]

    def test_signup_duplicate_student(self):
        """Test signup fails when student already registered"""
        # First signup should work
        response1 = client.post(
            "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200

        # Second signup with same email should fail
        response2 = client.post(
            "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_nonexistent_activity(self):
        """Test signup fails for non-existent activity"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_adds_to_participants_list(self):
        """Test that signup actually adds to participants list"""
        email = "testuser@mergington.edu"
        initial_count = len(activities["Basketball Club"]["participants"])

        response = client.post(
            f"/activities/Basketball%20Club/signup?email={email}"
        )
        assert response.status_code == 200

        final_count = len(activities["Basketball Club"]["participants"])
        assert final_count == initial_count + 1
        assert email in activities["Basketball Club"]["participants"]


class TestUnregisterEndpoint:
    """Test suite for the unregister/delete endpoint"""

    def setup_method(self):
        """Setup test data before each test"""
        self.original_participants = {}
        for activity_name, activity_data in activities.items():
            self.original_participants[activity_name] = activity_data["participants"].copy()

    def teardown_method(self):
        """Restore original participants after each test"""
        for activity_name, original_list in self.original_participants.items():
            activities[activity_name]["participants"] = original_list.copy()

    def test_unregister_success(self):
        """Test successful unregister"""
        activity_name = "Chess Club"
        email = activities[activity_name]["participants"][0]

        response = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email not in activities[activity_name]["participants"]

    def test_unregister_not_registered(self):
        """Test unregister fails for non-registered student"""
        response = client.delete(
            "/activities/Chess%20Club/participants?email=notregistered@mergington.edu"
        )
        assert response.status_code == 404
        assert "not registered" in response.json()["detail"]

    def test_unregister_nonexistent_activity(self):
        """Test unregister fails for non-existent activity"""
        response = client.delete(
            "/activities/NonExistent%20Activity/participants?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_removes_from_participants_list(self):
        """Test that unregister actually removes from participants list"""
        activity_name = "Programming Class"
        email = activities[activity_name]["participants"][0]
        initial_count = len(activities[activity_name]["participants"])

        response = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )
        assert response.status_code == 200

        final_count = len(activities[activity_name]["participants"])
        assert final_count == initial_count - 1
        assert email not in activities[activity_name]["participants"]


class TestRootEndpoint:
    """Test suite for the root endpoint"""

    def test_root_redirect(self):
        """Test root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestIntegrationScenarios:
    """Integration tests for realistic workflows"""

    def setup_method(self):
        """Setup test data before each test"""
        self.original_participants = {}
        for activity_name, activity_data in activities.items():
            self.original_participants[activity_name] = activity_data["participants"].copy()

    def teardown_method(self):
        """Restore original participants after each test"""
        for activity_name, original_list in self.original_participants.items():
            activities[activity_name]["participants"] = original_list.copy()

    def test_signup_then_unregister_workflow(self):
        """Test signup followed by unregister"""
        activity = "Soccer Team"
        email = "workflow@mergington.edu"

        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        assert email in activities[activity]["participants"]

        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/participants?email={email}"
        )
        assert unregister_response.status_code == 200
        assert email not in activities[activity]["participants"]

    def test_multiple_signups_to_different_activities(self):
        """Test student signing up to multiple activities"""
        email = "multiactivity@mergington.edu"
        activities_to_join = ["Art Club", "Drama Club", "Debate Team"]

        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200

        # Verify student is in all activities
        for activity in activities_to_join:
            assert email in activities[activity]["participants"]

    def test_participant_count_accuracy(self):
        """Test that participant counts remain accurate"""
        email1 = "count1@mergington.edu"
        email2 = "count2@mergington.edu"
        activity = "Science Club"

        initial_count = len(activities[activity]["participants"])

        # Sign up first student
        client.post(f"/activities/{activity}/signup?email={email1}")
        assert len(activities[activity]["participants"]) == initial_count + 1

        # Sign up second student
        client.post(f"/activities/{activity}/signup?email={email2}")
        assert len(activities[activity]["participants"]) == initial_count + 2

        # Unregister first student
        client.delete(f"/activities/{activity}/participants?email={email1}")
        assert len(activities[activity]["participants"]) == initial_count + 1

        # Unregister second student
        client.delete(f"/activities/{activity}/participants?email={email2}")
        assert len(activities[activity]["participants"]) == initial_count
