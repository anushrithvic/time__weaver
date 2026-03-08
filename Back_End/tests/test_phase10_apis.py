"""
Integration Tests for Phase 10 APIs
Tests all Module 3 timetable generation endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.db.session import get_db


# ============================================================================
# FIXTURES
# ============================================================================




# ============================================================================
# INSTITUTIONAL RULES API TESTS
# ============================================================================

class TestInstitutionalRulesAPI:
    """Test /api/v1/rules endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_rule(self, client: AsyncClient, auth_headers: dict):
        """Test creating an institutional rule"""
        import uuid
        rule_data = {
            "name": f"No Early Morning Classes {uuid.uuid4()}",
            "description": "Classes should not start before 9 AM",
            "rule_type": "TIME_WINDOW",
            "configuration": {"min_slot": 2, "max_slot": 8},
            "is_hard_constraint": True,
            "weight": 1.0,
            "applies_to_departments": [],
            "applies_to_years": [],
            "is_active": True
        }
        
        response = await client.post(
            "/api/v1/rules/",
            json=rule_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == rule_data["name"]
        assert data["rule_type"] == "TIME_WINDOW"
        assert "id" in data
        
        return data["id"]  # Return ID for other tests
    
    @pytest.mark.asyncio
    async def test_list_rules(self, client: AsyncClient, auth_headers: dict):
        """Test listing institutional rules"""
        response = await client.get(
            "/api/v1/rules/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)
    
    @pytest.mark.asyncio
    async def test_get_rule(self, client: AsyncClient, auth_headers: dict):
        """Test getting specific rule"""
        # First create a rule
        rule_id = await self.test_create_rule(client, auth_headers)
        
        # Then get it
        response = await client.get(
            f"/api/v1/rules/{rule_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == rule_id
    
    @pytest.mark.asyncio
    async def test_update_rule(self, client: AsyncClient, auth_headers: dict):
        """Test updating a rule"""
        # Create rule first
        rule_id = await self.test_create_rule(client, auth_headers)
        
        # Update it
        update_data = {"weight": 0.8, "is_active": False}
        response = await client.put(
            f"/api/v1/rules/{rule_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["weight"] == 0.8
        assert data["is_active"] is False
    
    @pytest.mark.asyncio
    async def test_toggle_rule(self, client: AsyncClient, auth_headers: dict):
        """Test toggling rule active status"""
        rule_id = await self.test_create_rule(client, auth_headers)
        
        # Get initial state
        response = await client.get(f"/api/v1/rules/{rule_id}", headers=auth_headers)
        initial_state = response.json()["is_active"]
        
        # Toggle
        response = await client.patch(
            f"/api/v1/rules/{rule_id}/toggle",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["is_active"] != initial_state
    
    @pytest.mark.asyncio
    async def test_delete_rule(self, client: AsyncClient, auth_headers: dict):
        """Test deleting a rule"""
        rule_id = await self.test_create_rule(client, auth_headers)
        
        response = await client.delete(
            f"/api/v1/rules/{rule_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify it's gone
        response = await client.get(f"/api/v1/rules/{rule_id}", headers=auth_headers)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_duplicate_name_error(self, client: AsyncClient, auth_headers: dict):
        """Test creating rule with duplicate name fails"""
        import uuid
        unique_name = f"Unique Test Rule {uuid.uuid4()}"
        rule_data = {
            "name": unique_name,
            "rule_type": "TIME_WINDOW",
            "configuration": {"min_slot": 1, "max_slot": 5},
            "is_hard_constraint": True,
            "weight": 1.0
        }
        
        # Create first rule
        response1 = await client.post("/api/v1/rules/", json=rule_data, headers=auth_headers)
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = await client.post("/api/v1/rules/", json=rule_data, headers=auth_headers)
        assert response2.status_code == 400
        assert "DUPLICATE_NAME" in response2.json()["detail"]["error"]


# ============================================================================
# TIMETABLE API TESTS
# ============================================================================

class TestTimetableAPI:
    """Test /api/v1/timetables endpoints"""
    
    @pytest.mark.asyncio
    async def test_list_timetables_empty(self, client: AsyncClient, auth_headers: dict):
        """Test listing timetables when none exist"""
        response = await client.get(
            "/api/v1/timetables/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)
    
    @pytest.mark.asyncio
    async def test_generate_timetable_missing_semester(self, client: AsyncClient, auth_headers: dict):
        """Test generation with non-existent semester"""
        gen_data = {
            "semester_id": 99999,
            "algorithm": "GA",
            "num_solutions": 3,
            "max_generations": 50
        }
        
        response = await client.post(
            "/api/v1/timetables/generate",
            json=gen_data,
            headers=auth_headers
        )
        
        # Should fail with 404 or 400
        assert response.status_code in [400, 404]
        assert "error" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_timetable(self, client: AsyncClient, auth_headers: dict):
        """Test getting timetable that doesn't exist"""
        response = await client.get(
            "/api/v1/timetables/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        error_data = response.json()["detail"]
        assert error_data["error"] == "NOT_FOUND"
        assert error_data["code"] == 404
    
    @pytest.mark.asyncio
    async def test_view_timetable_with_filters(self, client: AsyncClient, auth_headers: dict):
        """Test viewing timetables with department/year/section filters"""
        response = await client.get(
            "/api/v1/timetables/view",
            params={
                "semester_id": 1,
                "department_id": 1,
                "year_level": 3,
                "section_name": "A"
            },
        headers=auth_headers
        )
        
        # If no published timetable exists, it returns 404
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "timetable" in data


# ============================================================================
# SLOT LOCKING API TESTS
# ============================================================================

class TestSlotLockingAPI:
    """Test /api/v1/slot-locks endpoints"""
    
    @pytest.mark.asyncio
    async def test_lock_slots_invalid_timetable(self, client: AsyncClient, auth_headers: dict):
        """Test locking slots for non-existent timetable"""
        lock_data = {
            "timetable_id": 99999,
            "slot_ids": [1, 2, 3]
        }
        
        response = await client.post(
            "/api/v1/slot-locks/lock",
            json=lock_data,
            headers=auth_headers
        )
        
        assert response.status_code in [400, 404]
    
    @pytest.mark.asyncio
    async def test_get_locked_slots_invalid_timetable(self, client: AsyncClient, auth_headers: dict):
        """Test getting locked slots for non-existent timetable"""
        response = await client.get(
            "/api/v1/slot-locks/locked",
            params={"timetable_id": 99999},
            headers=auth_headers
        )
        
        assert response.status_code in [400, 404]


# ============================================================================
# FACULTY LEAVE API TESTS
# ============================================================================

class TestFacultyLeaveAPI:
    """Test /api/v1/faculty-leaves endpoints"""
    
    @pytest.mark.asyncio
    async def test_list_leaves_empty(self, client: AsyncClient, auth_headers: dict):
        """Test listing faculty leaves when none exist"""
        response = await client.get(
            "/api/v1/faculty-leaves/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 0
    
    @pytest.mark.asyncio
    async def test_analyze_leave_invalid_data(self, client: AsyncClient, auth_headers: dict):
        """Test leave analysis with invalid data"""
        analysis_data = {
            "faculty_id": 99999,
            "timetable_id": 99999,
            "start_date": "2024-10-01",
            "end_date": "2024-10-07",
            "leave_type": "SICK",
            "strategy": "WITHIN_SECTION_SWAP"
        }
        
        response = await client.post(
            "/api/v1/faculty-leaves/analyze",
            json=analysis_data,
            headers=auth_headers
        )
        
        # Should fail with 404 or 400
        assert response.status_code in [400, 404]


# ============================================================================
# PERMISSIONS TESTS
# ============================================================================

class TestPermissions:
    """Test role-based access control"""
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test accessing endpoints without authentication"""
        # Try to list rules without auth
        response = await client.get("/api/v1/rules/")
        # FastAPI may redirect to login (307) or return 401
        assert response.status_code in [401, 307]
        
        # Try to create rule without auth
        response = await client.post(
            "/api/v1/rules/",
            json={"name": "Test", "rule_type": "TIME_WINDOW", "configuration": {}}
        )
        assert response.status_code in [401, 307]


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test structured error responses"""
    
    @pytest.mark.asyncio
    async def test_structured_error_format(self, client: AsyncClient, auth_headers: dict):
        """Test that errors have correct structure"""
        response = await client.get(
            "/api/v1/timetables/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        error_detail = response.json()["detail"]
        
        # Check structured error format
        assert "error" in error_detail
        assert "message" in error_detail
        assert "code" in error_detail
        assert error_detail["code"] == 404
        assert error_detail["error"] == "NOT_FOUND"


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
