// API Configuration
const API_BASE_URL = 'http://localhost:3000/api';

// State
let curriculumEntries = [];
let departments = [];
let courses = [];
let filteredCurriculum = [];
let editingCurriculumId = null;

// Helper function to get auth token
function getAuthToken() {
    return localStorage.getItem('token');
}

// Helper function to make API calls
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        }
    };

    const token = getAuthToken();
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }

    if (data) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'API request failed');
    }

    return await response.json();
}

// Initialize page
window.onload = async function() {
    try {
        await loadDepartments();
        await loadCourses();
        await loadCurriculum();
        renderCurriculum();
        updateStats();
    } catch (error) {
        console.error('Error initializing page:', error);
        alert('Failed to load data: ' + error.message);
    }
};

// Load departments from API
async function loadDepartments() {
    try {
        const response = await apiCall('/departments/');
        departments = Array.isArray(response) ? response : response.data || [];
        const filterSelect = document.getElementById('filterDepartment');
        const curriculumSelect = document.getElementById('curriculumDepartment');

        // Clear existing options except the first one
        filterSelect.innerHTML = '<option value="">All Departments</option>';
        curriculumSelect.innerHTML = '<option value="">Select Department</option>';

        departments.forEach(dept => {
            const option1 = new Option(dept.name, dept.id);
            const option2 = new Option(dept.name, dept.id);
            filterSelect.add(option1);
            curriculumSelect.add(option2);
        });
    } catch (error) {
        console.error('Error loading departments:', error);
        throw error;
    }
}

// Load courses from API
async function loadCourses() {
    try {
        const response = await apiCall('/courses/');
        courses = Array.isArray(response) ? response : response.data || [];
    } catch (error) {
        console.error('Error loading courses:', error);
        throw error;
    }
}

// Load curriculum from API
async function loadCurriculum() {
    try {
        const response = await apiCall('/curriculum/');
        curriculumEntries = Array.isArray(response) ? response : response.data || [];

        // Enrich with department and course names
        curriculumEntries = curriculumEntries.map(entry => {
            const dept = departments.find(d => d.id === entry.department_id);
            const course = courses.find(c => c.id === entry.course_id);
            return {
                ...entry,
                department_name: dept ? dept.name : 'Unknown',
                course_code: course ? course.code : 'Unknown',
                course_name: course ? course.name : 'Unknown'
            };
        });
        filteredCurriculum = [...curriculumEntries];
    } catch (error) {
        console.error('Error loading curriculum:', error);
        throw error;
    }
}

// Render curriculum table
function renderCurriculum() {
    const tbody = document.getElementById('curriculumTableBody');

    if (filteredCurriculum.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No curriculum mappings found</td></tr>';
        return;
    }

    tbody.innerHTML = filteredCurriculum.map(entry => `
        <tr>
            <td>${entry.department_name}</td>
            <td>${entry.year_level}<sup>${getOrdinalSuffix(entry.year_level)}</sup> Year</td>
            <td>
                <span class="badge ${entry.semester_type === 'ODD' ? 'badge-info' : 'badge-success'}">
                    ${entry.semester_type}
                </span>
            </td>
            <td><strong>${entry.course_code}</strong></td>
            <td>${entry.course_name}</td>
            <td>
                <span class="badge ${entry.is_mandatory ? 'badge-secondary' : 'badge-success'}">
                    ${entry.is_mandatory ? 'Core' : 'Elective'}
                </span>
            </td>
            <td class="actions">
                <button class="btn-edit" onclick="editCurriculum(${entry.id})">Edit</button>
                <button class="btn-danger" onclick="deleteCurriculum(${entry.id})">Delete</button>
            </td>
        </tr>
    `).join('');
}

// Helper function for ordinal suffixes
function getOrdinalSuffix(num) {
    const j = num % 10;
    const k = num % 100;
    if (j === 1 && k !== 11) return 'st';
    if (j === 2 && k !== 12) return 'nd';
    if (j === 3 && k !== 13) return 'rd';
    return 'th';
}

// Update statistics
function updateStats() {
    document.getElementById('totalMappings').textContent = curriculumEntries.length;
    document.getElementById('coreCourses').textContent = curriculumEntries.filter(c => c.is_mandatory).length;
    document.getElementById('electiveCourses').textContent = curriculumEntries.filter(c => !c.is_mandatory).length;
}

// Search curriculum
function searchCurriculum() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    filteredCurriculum = curriculumEntries.filter(entry =>
        entry.department_name.toLowerCase().includes(searchTerm) ||
        entry.course_code.toLowerCase().includes(searchTerm) ||
        entry.course_name.toLowerCase().includes(searchTerm)
    );
    renderCurriculum();
}

// Apply filters
function applyFilters() {
    const deptFilter = document.getElementById('filterDepartment').value;
    const yearFilter = document.getElementById('filterYear').value;
    const semesterFilter = document.getElementById('filterSemester').value;

    filteredCurriculum = curriculumEntries.filter(entry => {
        if (deptFilter && entry.department_id != deptFilter) return false;
        if (yearFilter && entry.year_level != yearFilter) return false;
        if (semesterFilter && entry.semester_type !== semesterFilter) return false;
        return true;
    });

    renderCurriculum();
}

// Clear filters
function clearFilters() {
    document.getElementById('filterDepartment').value = '';
    document.getElementById('filterYear').value = '';
    document.getElementById('filterSemester').value = '';
    document.getElementById('searchInput').value = '';
    filteredCurriculum = [...curriculumEntries];
    renderCurriculum();
}

// Open add modal
function openAddModal() {
    editingCurriculumId = null;
    document.getElementById('modalTitle').textContent = 'Add Curriculum Mapping';
    document.getElementById('curriculumForm').reset();
    document.getElementById('curriculumId').value = '';
    document.getElementById('isMandatory').checked = true;

    // Populate course dropdown
    updateCourseDropdown();

    document.getElementById('curriculumModal').classList.add('active');
}

// Edit curriculum
function editCurriculum(id) {
    const entry = curriculumEntries.find(c => c.id === id);
    if (!entry) return;

    editingCurriculumId = id;
    document.getElementById('modalTitle').textContent = 'Edit Curriculum Mapping';
    document.getElementById('curriculumId').value = entry.id;
    document.getElementById('curriculumDepartment').value = entry.department_id;
    document.getElementById('curriculumYear').value = entry.year_level;
    document.getElementById('curriculumSemester').value = entry.semester_type;
    document.getElementById('curriculumCourse').value = entry.course_id;
    document.getElementById('isMandatory').checked = entry.is_mandatory;

    document.getElementById('curriculumModal').classList.add('active');
}

// Delete curriculum
async function deleteCurriculum(id) {
    if (!confirm('Are you sure you want to delete this curriculum mapping?')) return;

    try {
        await apiCall(`/curriculum/${id}`, 'DELETE');
        curriculumEntries = curriculumEntries.filter(c => c.id !== id);
        filteredCurriculum = filteredCurriculum.filter(c => c.id !== id);
        renderCurriculum();
        updateStats();
        alert('Curriculum mapping deleted successfully');
    } catch (error) {
        console.error('Error deleting curriculum:', error);
        alert('Failed to delete curriculum mapping: ' + error.message);
    }
}

// Update course dropdown based on selected department
function updateCourseDropdown() {
    const deptId = parseInt(document.getElementById('curriculumDepartment').value);
    const courseSelect = document.getElementById('curriculumCourse');

    courseSelect.innerHTML = '<option value="">Select Course</option>';

    if (!deptId) return;

    const deptCourses = courses.filter(c => c.department_id == deptId);
    deptCourses.forEach(course => {
        const option = new Option(`${course.code} - ${course.name}`, course.id);
        courseSelect.add(option);
    });
}

// Listen to department change to update courses
document.addEventListener('DOMContentLoaded', function() {
    const deptSelect = document.getElementById('curriculumDepartment');
    if (deptSelect) {
        deptSelect.addEventListener('change', updateCourseDropdown);
    }
});

// Save curriculum
async function saveCurriculum(event) {
    event.preventDefault();

    const deptId = parseInt(document.getElementById('curriculumDepartment').value);
    const yearLevel = parseInt(document.getElementById('curriculumYear').value);
    const semesterType = document.getElementById('curriculumSemester').value;
    const courseId = parseInt(document.getElementById('curriculumCourse').value);
    const isMandatory = document.getElementById('isMandatory').checked;

    // Validate required fields
    if (!deptId || !yearLevel || !semesterType || !courseId) {
        alert('Please fill in all required fields');
        return;
    }

    // API expects these exact fields
    const curriculumData = {
        department_id: deptId,
        year_level: yearLevel,
        semester_type: semesterType,
        course_id: courseId,
        is_mandatory: isMandatory
    };

    try {
        let savedCurriculum;
        if (editingCurriculumId) {
            savedCurriculum = await apiCall(`/curriculum/${editingCurriculumId}`, 'PUT', curriculumData);
        } else {
            savedCurriculum = await apiCall('/curriculum/', 'POST', curriculumData);
        }

        // Reload curriculum from API
        await loadCurriculum();
        renderCurriculum();
        updateStats();
        closeModal();
        alert('Curriculum mapping saved successfully');
    } catch (error) {
        console.error('Error saving curriculum:', error);
        alert('Failed to save curriculum mapping: ' + error.message);
    }
}

// Close modal
function closeModal() {
    document.getElementById('curriculumModal').classList.remove('active');
    document.getElementById('curriculumForm').reset();
    editingCurriculumId = null;
}

// Close modal on outside click
window.onclick = function(event) {
    const modal = document.getElementById('curriculumModal');
    if (event.target === modal) {
        closeModal();
    }
};
