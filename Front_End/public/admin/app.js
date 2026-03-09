// --- DATA LAYER ---
// We will fetch these dynamically upon initialization instead of locally.
let facultyData = [];
let studentData = [];
let institutionData = { name: 'Amrita Vishwa Vidyapeetham, Coimbatore', year: '2025-2026' };
let roomData = [];
let ruleData = [];
let timetableData = [];

// --- UI HELPERS ---
function toggleModal(id, show) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.toggle('hidden', !show);
}

function showPage(pageId) {
    document.querySelectorAll('.page-content').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.sidebar-item').forEach(b => b.classList.remove('active'));

    const page = document.getElementById(`page-${pageId}`);
    if (page) page.classList.remove('hidden');

    const btn = document.getElementById(`btn-${pageId}`);
    if (btn) btn.classList.add('active');

    // Load data for academic setup pages
    if (pageId === 'overview') updateStats();
    if (pageId === 'departments') loadDepartments();
    if (pageId === 'courses') {
        loadDepartments();
        loadCourses();
    }
    if (pageId === 'semesters') loadSemesters();
    if (pageId === 'sections') {
        loadDepartments();
        loadSections();
    }
    if (pageId === 'rooms') loadRooms();
    if (pageId === 'institution') loadRules();
}

// Faculty and Student loads are now handled by loadUsers in admin-pages.js

async function loadRooms() {
    try {
        const response = await API.get('/rooms/');
        roomData = response.data || response;
        renderRooms();
    } catch (error) {
        console.error('Error loading rooms:', error);
    }
}

async function loadRules() {
    try {
        const response = await API.get('/rules/');
        ruleData = response.data || response;
        renderRules();
    } catch (error) {
        console.error('Error loading rules:', error);
    }
}

// Removed deprecated Faculty and Student JS logic directly handling local storage
// User CRUD is fully mediated via `admin-pages.js` User Management page

// --- ROOM LOGIC ---
async function saveRoom() {
    const building = document.getElementById('room-building').value;
    const number = document.getElementById('room-number').value;
    const type = document.getElementById('room-type').value;
    const capacity = parseInt(document.getElementById('room-capacity').value);

    // Checkboxes
    const hasProjector = document.getElementById('room-projector').checked;
    const hasLab = document.getElementById('room-lab').checked;
    const hasAC = document.getElementById('room-ac').checked;

    if (!building || !number || !capacity) return alert("Please fill required fields (Building, Number, Capacity)");

    try {
        await API.post('/rooms/', {
            room_number: number,
            building: building,
            capacity: capacity,
            room_type: type,
            has_projector: hasProjector,
            has_lab_equipment: hasLab,
            has_ac: hasAC
        });
        toggleModal('modal-room', false);
        document.getElementById('room-building').value = '';
        document.getElementById('room-number').value = '';
        loadRooms();
    } catch (err) {
        console.error('Error saving room:', err);
        alert('Failed to save room details');
    }
}

async function deleteRoom(id) {
    if (!confirm('Are you sure you want to delete this room?')) return;
    try {
        await API.del(`/rooms/${id}`);
        loadRooms();
    } catch (err) {
        console.error('Error deleting room:', err);
        alert('Failed to delete room');
    }
}

function renderRooms() {
    const list = document.getElementById('room-list');
    if (!list) return;
    list.innerHTML = roomData.map(r => `
        <tr class="hover:bg-main transition-colors border-b border-border-color last:border-0">
            <td class="px-8 py-5 font-bold text-text-main">${r.full_name || r.building + '-' + r.room_number}</td>
            <td class="px-8 py-5 text-text-muted text-sm font-medium">
                <span class="bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 px-2 py-1 rounded-md text-xs uppercase font-bold tracking-wider">${r.room_type}</span>
            </td>
            <td class="px-8 py-5 text-text-muted text-sm font-medium">${r.capacity}</td>
            <td class="px-8 py-5 text-text-muted text-sm font-medium">
                <div class="flex gap-2">
                    ${r.has_projector ? '<i class="fa-solid fa-video text-cyan-500/50" title="Projector"></i>' : ''}
                    ${r.has_lab_equipment ? '<i class="fa-solid fa-flask text-fuchsia-500/50" title="Lab Equipment"></i>' : ''}
                    ${r.has_ac ? '<i class="fa-solid fa-snowflake text-blue-500/50" title="AC"></i>' : ''}
                </div>
            </td>
            <td class="px-8 py-5 text-center">
                <button onclick="deleteRoom(${r.id})" class="text-text-muted hover:text-red-400 transition-colors">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </td>
        </tr>
    `).join('');
}


// --- INSTITUTION & RULES LOGIC ---
function saveInstitution() {
    const name = document.getElementById('inst-name').value;
    const year = document.getElementById('inst-year').value;
    institutionData = { ...institutionData, name, year };
    localStorage.setItem('timeWeaver_institution', JSON.stringify(institutionData));
    alert("Settings Saved!");
    document.title = `${name} Admin | v1.0`;
}

async function saveRule() {
    const name = document.getElementById('rule-name').value;
    const type = document.getElementById('rule-type').value;
    const weight = document.getElementById('rule-weight').value;
    const desc = document.getElementById('rule-desc').value;
    const isHard = document.getElementById('rule-hard').checked;

    if (!name) return alert("Rule Name is required");

    try {
        await API.post('/rules/', {
            name: name,
            rule_type: type,
            description: desc,
            weight: parseFloat(weight) || 1.0,
            is_hard_constraint: isHard,
            is_active: true
        });
        toggleModal('modal-rule', false);
        document.getElementById('rule-name').value = '';
        document.getElementById('rule-desc').value = '';
        loadRules();
    } catch (err) {
        console.error('Error saving rule:', err);
        alert('Failed to save rule');
    }
}

async function deleteRule(id) {
    if (!confirm('Are you sure you want to delete this rule?')) return;
    try {
        await API.del(`/rules/${id}`);
        loadRules();
    } catch (err) {
        console.error('Error deleting rule:', err);
        alert('Failed to delete rule');
    }
}

function renderRules() {
    const list = document.getElementById('rule-list');
    if (!list) return;
    list.innerHTML = ruleData.map(r => `
        <div class="bg-main p-4 rounded-xl border border-border-color flex justify-between items-center mb-3 hover:border-text-muted transition-all">
            <div>
                <div class="flex items-center gap-2 mb-1">
                    <h4 class="font-bold text-text-main">${r.name}</h4>
                    ${r.is_hard_constraint
            ? '<span class="bg-red-500/10 text-red-400 text-[10px] px-2 py-0.5 rounded font-bold uppercase border border-red-500/20">Hard</span>'
            : '<span class="bg-blue-500/10 text-blue-400 text-[10px] px-2 py-0.5 rounded font-bold uppercase border border-blue-500/20">Soft</span>'}
                </div>
                <p class="text-xs text-text-muted">${r.description || 'No description'}</p>
                <div class="mt-2 text-[10px] font-mono text-text-muted bg-card inline-block px-2 py-1 rounded border border-border-color">
                    Type: ${r.rule_type} | Weight: ${r.weight}
                </div>
            </div>
            <button onclick="deleteRule(${r.id})" class="text-text-muted hover:text-red-400 transition-colors px-3">
                <i class="fa-solid fa-trash-can"></i>
            </button>
        </div>
    `).join('');
}

function loadInstitution() {
    if (document.getElementById('inst-name')) {
        document.getElementById('inst-name').value = institutionData.name || '';
        document.getElementById('inst-year').value = institutionData.year || '';
    }
    renderRules();
}

async function updateStats() {
    try {
        // 1. Total Faculty
        if (document.getElementById('stat-faculty-count')) {
            const facReq = await API.get('/users/?role=faculty');
            document.getElementById('stat-faculty-count').innerText = Array.isArray(facReq) ? facReq.length : (facReq.total || 0);
        }

        // 2. Total Students
        if (document.getElementById('stat-student-count')) {
            const stuReq = await API.get('/users/?role=student');
            document.getElementById('stat-student-count').innerText = Array.isArray(stuReq) ? stuReq.length : (stuReq.total || 0);
        }

        // 3. Critical Conflicts
        const critConflicts = mockConflicts.filter(c => c.severity === 'critical' && c.status === 'open').length;
        if (document.getElementById('stat-critical-conflicts')) {
            document.getElementById('stat-critical-conflicts').innerText = critConflicts;
        }

        // 4. Pending Leave Requests
        if (document.getElementById('stat-pending-leaves')) {
            const leavesReq = await API.get('/faculty-leaves/');
            const leavesArray = Array.isArray(leavesReq) ? leavesReq : (leavesReq.data || []);
            document.getElementById('stat-pending-leaves').innerText = leavesArray.filter(l => l.status === 'PENDING').length;
        }
    } catch (err) {
        console.error("Error updating dashboard stats: ", err);
    }
}

// --- TIMETABLE LOGIC ---
function getFilterCriteria() {
    return {
        year: document.getElementById('tt-year').value,
        program: document.getElementById('tt-program').value,
        dept: document.getElementById('tt-dept').value,
        sem: document.getElementById('tt-sem').value,
        section: document.getElementById('tt-sec').value
    };
}

async function generateTimetable(mode) {
    const criteria = getFilterCriteria();
    const { year, program, dept, sem, section } = criteria;

    if (!confirm(`Are you sure you want to ${mode} the schedule for ${program} ${dept} Sem-${sem} Sec-${section}? This will rely on the backend constraints.`)) return;

    try {
        await API.post('/timetables/generate', {
            semester_id: parseInt(sem) || 1,
            num_solutions: 1
        });
        alert("Timetable generation request sent to backend!");
        loadTimetable(true);
    } catch (error) {
        console.error('Error generating timetable:', error);
        alert("Generation failed, please check backend logs.");
    }
}

async function loadTimetable(isFiltered = false) {
    const times = [
        "08:00 - 08:50", "08:50 - 09:40", "09:40 - 10:30",
        "10:45 - 11:35", "11:35 - 12:25", "12:25 - 01:15",
        "02:05 - 02:55", "02:55 - 03:45", "03:45 - 04:35",
        "04:35 - 05:25", "05:25 - 06:15"
    ];
    const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

    try {
        // We fetch all for demo. In prod, we'd use ?semester_id=..
        const fetchedData = await API.get('/timetables/');

        // We'll map the backend timetable structure to the frontend structure if needed
        // The exact structure of GET /timetables/ depends on the backend, assuming it returns an array of slots or timetables.
        // For demonstration, if we get an array of timetables, we might take the first one:
        let displayData = [];
        if (fetchedData.length > 0) {
            // Fallback to empty if structure is complex
            displayData = fetchedData[0].slots || [];
        }

        const body = document.getElementById('timetable-body');
        if (!body) return;

        body.innerHTML = times.map(time => `
            <div class="timetable-grid border-b border-border-color">
                <div class="p-6 border-r border-border-color text-xs font-black text-text-muted flex items-center justify-center">${time}</div>
                ${days.map(day => {
            const classSession = displayData.find(t => t.day_of_week === day && t.start_time.startsWith(time.split(' - ')[0]));

            return `
                        <div class="p-3 border-r border-border-color h-32 transition-colors hover:bg-main">
                            ${classSession ? `
                                <div class="bg-card border border-border-color p-4 rounded-2xl h-full shadow-sm flex flex-col justify-between group hover:border-cyan-500/50 hover:shadow-lg hover:shadow-cyan-900/20 transition-all">
                                    <div>
                                        <p class="text-[9px] font-black text-cyan-400 tracking-tighter uppercase mb-1 neon-text">Lecture</p>
                                        <p class="text-[13px] font-extrabold text-text-main leading-tight">${classSession.course_name || classSession.subject || 'Course'}</p>
                                        <p class="text-[10px] text-text-muted mt-1 font-semibold">${classSession.faculty_name || classSession.faculty || 'Faculty'}</p>
                                    </div>
                                    <div class="flex justify-between items-end">
                                        <span class="text-[10px] text-text-muted font-bold">${classSession.room_name || classSession.room || 'Room'}</span>
                                        <i class="fa-solid fa-circle-check text-green-500 text-xs opacity-0 group-hover:opacity-100 transition-opacity"></i>
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    `;
        }).join('')}
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading timetables:', error);
    }
}

// --- CONFLICT MONITOR LOGIN ---
let mockConflicts = [
    {
        id: 'C-101',
        type: 'ROOM_DOUBLE_BOOKING',
        severity: 'critical',
        title: 'Room 304 Double Booked',
        description: 'CS-202 (Data Structures) and CS-301 (OS) are scheduled at the same time.',
        time: 'Mon, 10:00 AM - 11:00 AM',
        location: 'Block A, Room 304',
        parties: ['Prof. Smith', 'Prof. Johnson'],
        status: 'open'
    },
    {
        id: 'C-102',
        type: 'FACULTY_OVERLAP',
        severity: 'critical',
        title: 'Faculty Schedule Conflict',
        description: 'Dr. Sarah Thorne is assigned to two classes simultaneously.',
        time: 'Tue, 02:00 PM - 03:30 PM',
        location: 'Labs 1 & 3',
        parties: ['Dr. Sarah Thorne'],
        status: 'open'
    },
    {
        id: 'C-103',
        type: 'CAPACITY_OVERFLOW',
        severity: 'warning',
        title: 'Room Capacity Exceeded',
        description: 'Class size (65) exceeds room capacity (50).',
        time: 'Wed, 09:00 AM',
        location: 'Room 101',
        parties: ['CS Year 1'],
        status: 'open'
    },
    {
        id: 'C-104',
        type: 'SECTION_OVERLAP',
        severity: 'warning',
        title: 'Section Overlap',
        description: 'Section A has two core subjects scheduled consecutively without break.',
        time: 'Thu, 11:00 AM',
        location: 'N/A',
        parties: ['Section A'],
        status: 'open'
    }
];

const conflictStats = {
    critical: 0,
    warnings: 0,
    resolved: 14
};

function getIconForType(type) {
    switch (type) {
        case 'ROOM_DOUBLE_BOOKING': return 'fa-building-circle-exclamation';
        case 'FACULTY_OVERLAP': return 'fa-user-clock';
        case 'CAPACITY_OVERFLOW': return 'fa-users-slash';
        default: return 'fa-circle-exclamation';
    }
}

function renderConflicts() {
    const container = document.getElementById('conflicts-container');
    if (!container) return;

    container.innerHTML = '';

    // Reset Stats for calculation
    let crit = 0;
    let warn = 0;

    mockConflicts.forEach(conflict => {
        if (conflict.status !== 'open') return;

        if (conflict.severity === 'critical') crit++;
        if (conflict.severity === 'warning') warn++;

        const card = document.createElement('div');
        // Animation class
        card.className = 'bg-card p-5 rounded-xl border border-l-4 shadow-sm hover:shadow-lg hover:shadow-card/50 transition-all cursor-pointer group relative';

        // Dynamic border color based on severity
        const borderColor = conflict.severity === 'critical' ? 'border-red-500/50 border-l-red-500' : 'border-amber-500/50 border-l-amber-500';
        const iconColor = conflict.severity === 'critical' ? 'text-red-500 bg-red-500/10' : 'text-amber-500 bg-amber-500/10';
        card.classList.add(...borderColor.split(' '));

        card.innerHTML = `
            <div class="flex items-start gap-4">
                <div class="w-12 h-12 rounded-lg ${iconColor} flex items-center justify-center shrink-0">
                    <i class="fa-solid ${getIconForType(conflict.type)} text-xl"></i>
                </div>
                
                <div class="flex-1">
                    <div class="flex items-center justify-between mb-1">
                        <h4 class="text-text-main font-bold text-lg flex items-center gap-2">
                            ${conflict.title}
                            ${conflict.severity === 'critical'
                ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20 tracking-wider">CRITICAL</span>'
                : '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 tracking-wider">WARNING</span>'}
                        </h4>
                        <span class="text-text-muted text-xs font-mono">#${conflict.id}</span>
                    </div>
                    
                    <p class="text-text-muted text-sm mb-3 font-medium">${conflict.description}</p>
                    
                    <div class="flex flex-wrap items-center gap-4 text-xs text-text-muted font-semibold">
                        <div class="flex items-center gap-1.5 bg-main border border-border-color px-2 py-1 rounded">
                            <i class="fa-regular fa-clock text-cyan-500"></i> ${conflict.time}
                        </div>
                        <div class="flex items-center gap-1.5 bg-main border border-border-color px-2 py-1 rounded">
                            <i class="fa-solid fa-location-dot text-cyan-500"></i> ${conflict.location}
                        </div>
                        <div class="flex items-center gap-1.5 bg-main border border-border-color px-2 py-1 rounded">
                            <i class="fa-solid fa-users text-cyan-500"></i> ${conflict.parties.join(', ')}
                        </div>
                    </div>
                </div>

                <div class="flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity absolute right-4 top-1/2 -translate-y-1/2 md:static md:opacity-100 md:translate-y-0">
                    <button onclick="resolveConflict('${conflict.id}')" class="p-2 bg-green-500/10 hover:bg-green-500 text-green-500 hover:text-white rounded-lg transition-colors border border-green-500/20 hover:border-green-500" title="Mark Resolved">
                        <i class="fa-solid fa-check"></i>
                    </button>
                </div>
            </div>
        `;
        container.appendChild(card);
    });

    // Update Stats UI
    if (document.getElementById('stat-critical')) document.getElementById('stat-critical').innerText = crit;
    if (document.getElementById('stat-warnings')) document.getElementById('stat-warnings').innerText = warn;
    if (document.getElementById('stat-resolved')) document.getElementById('stat-resolved').innerText = conflictStats.resolved;
}

window.resolveConflict = function (id) {
    const idx = mockConflicts.findIndex(c => c.id === id);
    if (idx !== -1) {
        mockConflicts[idx].status = 'resolved';
        conflictStats.resolved++;
        renderConflicts();
    }
};

const API_BASE = 'http://127.0.0.1:8001/api/v1';

// Helper: fetch with JWT auth header
function authFetch(url, options = {}) {
    const token = localStorage.getItem('token');
    const headers = {
        ...(options.headers || {}),
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
    return fetch(url, { ...options, headers });
}

// DEPARTMENTS
let departmentsData = [];

async function loadDepartments() {
    try {
        const response = await authFetch(`${API_BASE}/departments`);
        const json = await response.json();
        departmentsData = json.data || json;
        renderDepartments();
        updateDepartmentDropdowns();
    } catch (error) {
        console.error('Error loading departments:', error);
    }
}

function renderDepartments() {
    const tbody = document.getElementById('departments-list');
    if (!tbody) return;

    tbody.innerHTML = departmentsData.map(dept => `
        <tr class="hover:bg-main transition-colors">
            <td class="px-8 py-4 font-mono text-sm text-cyan-400 font-bold">${dept.code}</td>
            <td class="px-8 py-4 text-text-main font-semibold">${dept.name}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${dept.description || '-'}</td>
            <td class="px-8 py-4 text-center flex items-center justify-center gap-2">
                <button onclick="editDepartment(${dept.id})" class="text-blue-400 hover:text-blue-300 transition-colors" title="Edit">
                    <i class="fa-solid fa-pen"></i>
                </button>
                <button onclick="deleteDepartment(${dept.id})" class="text-red-400 hover:text-red-300 transition-colors" title="Delete">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

let editingDeptId = null;

function editDepartment(id) {
    const dept = departmentsData.find(d => d.id === id);
    if (!dept) return;

    editingDeptId = id;
    document.getElementById('dept-code').value = dept.code || '';
    document.getElementById('dept-name').value = dept.name || '';
    document.getElementById('dept-desc').value = dept.description || '';
    toggleModal('modal-department', true);
}

async function saveDepartment() {
    const code = document.getElementById('dept-code').value;
    const name = document.getElementById('dept-name').value;
    const description = document.getElementById('dept-desc').value;

    if (!code || !name) return alert('Please fill in required fields');

    try {
        const url = editingDeptId ? `${API_BASE}/departments/${editingDeptId}` : `${API_BASE}/departments/`;
        const method = editingDeptId ? 'PUT' : 'POST';

        const response = await authFetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, name, description })
        });

        if (response.ok) {
            toggleModal('modal-department', false);
            document.getElementById('dept-code').value = '';
            document.getElementById('dept-name').value = '';
            document.getElementById('dept-desc').value = '';
            editingDeptId = null;
            loadDepartments();
        } else {
            const data = await response.json();
            alert(data.detail || data.error || 'Failed to save department');
        }
    } catch (error) {
        console.error('Error saving department:', error);
        alert('Error saving department');
    }
}

async function deleteDepartment(id) {
    if (!confirm('Are you sure you want to delete this department?')) return;

    try {
        const response = await authFetch(`${API_BASE}/departments/${id}`, { method: 'DELETE' });
        if (response.ok) {
            loadDepartments();
        }
    } catch (error) {
        console.error('Error deleting department:', error);
    }
}

function updateDepartmentDropdowns() {
    const selects = [document.getElementById('course-dept'), document.getElementById('section-dept')];
    selects.forEach(select => {
        if (select) {
            select.innerHTML = '<option value="">Select Department</option>' +
                departmentsData.map(dept => `<option value="${dept.id}">${dept.name}</option>`).join('');
        }
    });
}

// COURSES
let coursesData = [];

async function loadCourses() {
    try {
        const response = await authFetch(`${API_BASE}/courses`);
        const json = await response.json();
        coursesData = json.data || json;
        renderCourses();
    } catch (error) {
        console.error('Error loading courses:', error);
    }
}

function renderCourses() {
    const tbody = document.getElementById('courses-list');
    if (!tbody) return;

    tbody.innerHTML = coursesData.map(course => `
        <tr class="hover:bg-main transition-colors">
            <td class="px-8 py-4 font-mono text-sm text-cyan-400 font-bold">${course.code}</td>
            <td class="px-8 py-4 text-text-main font-semibold">${course.name}</td>
            <td class="px-8 py-4 text-text-main text-center">${course.credits}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${course.theory_hours || 0}/${course.lab_hours || 0}/${course.tutorial_hours || 0}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${course.department_name || '-'}</td>
            <td class="px-8 py-4 text-center flex items-center justify-center gap-2">
                <button onclick="editCourse(${course.id})" class="text-blue-400 hover:text-blue-300 transition-colors" title="Edit">
                    <i class="fa-solid fa-pen"></i>
                </button>
                <button onclick="deleteCourse(${course.id})" class="text-red-400 hover:text-red-300 transition-colors" title="Delete">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

let editingCourseId = null;

function editCourse(id) {
    const course = coursesData.find(c => c.id === id);
    if (!course) return;

    editingCourseId = id;
    document.getElementById('course-code').value = course.code || '';
    document.getElementById('course-name').value = course.name || '';
    document.getElementById('course-credits').value = course.credits || '';
    document.getElementById('course-theory').value = course.theory_hours || 0;
    document.getElementById('course-lab').value = course.lab_hours || 0;
    document.getElementById('course-tutorial').value = course.tutorial_hours || 0;
    document.getElementById('course-dept').value = course.department_id || '';
    document.getElementById('course-lab-required').checked = !!course.requires_lab;
    toggleModal('modal-course', true);
}

async function saveCourse() {
    const code = document.getElementById('course-code').value;
    const name = document.getElementById('course-name').value;
    const credits = document.getElementById('course-credits').value;
    const theory_hours = document.getElementById('course-theory').value;
    const lab_hours = document.getElementById('course-lab').value;
    const tutorial_hours = document.getElementById('course-tutorial').value;
    const department_id = document.getElementById('course-dept').value;
    const requires_lab = document.getElementById('course-lab-required').checked;

    if (!code || !name || !credits || !department_id) return alert('Please fill in required fields');

    try {
        const url = editingCourseId ? `${API_BASE}/courses/${editingCourseId}` : `${API_BASE}/courses/`;
        const method = editingCourseId ? 'PUT' : 'POST';

        const response = await authFetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, name, credits: parseInt(credits), theory_hours: parseInt(theory_hours), lab_hours: parseInt(lab_hours), tutorial_hours: parseInt(tutorial_hours), department_id: parseInt(department_id), requires_lab })
        });

        if (response.ok) {
            toggleModal('modal-course', false);
            document.getElementById('course-code').value = '';
            document.getElementById('course-name').value = '';
            document.getElementById('course-credits').value = '';
            document.getElementById('course-theory').value = '0';
            document.getElementById('course-lab').value = '0';
            document.getElementById('course-tutorial').value = '0';
            document.getElementById('course-dept').value = '';
            document.getElementById('course-lab-required').checked = false;
            editingCourseId = null;
            loadCourses();
        } else {
            const data = await response.json();
            alert(data.detail || data.error || 'Failed to save course');
        }
    } catch (error) {
        console.error('Error saving course:', error);
        alert('Error saving course');
    }
}

async function deleteCourse(id) {
    if (!confirm('Are you sure you want to delete this course?')) return;

    try {
        const response = await authFetch(`${API_BASE}/courses/${id}`, { method: 'DELETE' });
        if (response.ok) {
            loadCourses();
        }
    } catch (error) {
        console.error('Error deleting course:', error);
    }
}

// SEMESTERS
let semestersData = [];

async function loadSemesters() {
    try {
        const response = await authFetch(`${API_BASE}/semesters`);
        const json = await response.json();
        semestersData = json.data || json;
        renderSemesters();
    } catch (error) {
        console.error('Error loading semesters:', error);
    }
}

function renderSemesters() {
    const tbody = document.getElementById('semesters-list');
    if (!tbody) return;

    tbody.innerHTML = semestersData.map(sem => `
        <tr class="hover:bg-main transition-colors">
            <td class="px-8 py-4 text-text-main font-semibold">${sem.academic_year || sem.year || sem.name}</td>
            <td class="px-8 py-4 text-text-main">Semester ${sem.semester_number || sem.semester_type || '-'}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${new Date(sem.start_date).toLocaleDateString()}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${new Date(sem.end_date).toLocaleDateString()}</td>
            <td class="px-8 py-4 text-center">
                <span class="px-3 py-1 rounded-full text-xs font-bold ${sem.is_active ? 'bg-green-500/10 text-green-400' : 'bg-gray-500/10 text-gray-400'}">
                    ${sem.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td class="px-8 py-4 text-center flex items-center justify-center gap-2">
                <button onclick="editSemester(${sem.id})" class="text-blue-400 hover:text-blue-300 transition-colors" title="Edit">
                    <i class="fa-solid fa-pen"></i>
                </button>
                <button onclick="deleteSemester(${sem.id})" class="text-red-400 hover:text-red-300 transition-colors" title="Delete">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

let editingSemesterId = null;

function editSemester(id) {
    const sem = semestersData.find(s => s.id === id);
    if (!sem) return;

    editingSemesterId = id;
    // Attempting to prepopulate input based on new naming or old naming fields
    document.getElementById('sem-year').value = sem.academic_year || sem.year || sem.name || '';
    document.getElementById('sem-number').value = sem.semester_number || sem.semester_type || '1';

    // Format date properly for inputs
    if (sem.start_date) document.getElementById('sem-start').value = new Date(sem.start_date).toISOString().split('T')[0];
    if (sem.end_date) document.getElementById('sem-end').value = new Date(sem.end_date).toISOString().split('T')[0];

    toggleModal('modal-semester', true);
}

async function saveSemester() {
    const year = document.getElementById('sem-year').value;
    const semester_number = document.getElementById('sem-number').value;
    const start_date = document.getElementById('sem-start').value;
    const end_date = document.getElementById('sem-end').value;

    if (!year || !semester_number || !start_date || !end_date) return alert('Please fill in all fields');

    try {
        const url = editingSemesterId ? `${API_BASE}/semesters/${editingSemesterId}` : `${API_BASE}/semesters/`;
        const method = editingSemesterId ? 'PUT' : 'POST';

        const payload = {
            name: `${year} Semester ${semester_number}`,
            academic_year: year,
            semester_type: isNaN(semester_number) ? semester_number : (semester_number % 2 === 0 ? "EVEN" : "ODD"), // Adapt for the updated schema
            start_date,
            end_date,
            is_active: true
        };

        const response = await authFetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            toggleModal('modal-semester', false);
            document.getElementById('sem-year').value = '';
            document.getElementById('sem-number').value = '1';
            document.getElementById('sem-start').value = '';
            document.getElementById('sem-end').value = '';
            editingSemesterId = null;
            loadSemesters();
        } else {
            const data = await response.json();
            alert(data.detail || data.error || 'Failed to save semester');
        }
    } catch (error) {
        console.error('Error saving semester:', error);
        alert('Error saving semester');
    }
}

async function deleteSemester(id) {
    if (!confirm('Are you sure you want to delete this semester?')) return;

    try {
        const response = await authFetch(`${API_BASE}/semesters/${id}`, { method: 'DELETE' });
        if (response.ok) {
            loadSemesters();
        }
    } catch (error) {
        console.error('Error deleting semester:', error);
    }
}

// SECTIONS
let sectionsData = [];

async function loadSections() {
    try {
        const response = await authFetch(`${API_BASE}/sections`);
        const json = await response.json();
        sectionsData = json.data || json;
        renderSections();
    } catch (error) {
        console.error('Error loading sections:', error);
    }
}

function renderSections() {
    const tbody = document.getElementById('sections-list');
    if (!tbody) return;

    tbody.innerHTML = sectionsData.map(section => `
        <tr class="hover:bg-main transition-colors">
            <td class="px-8 py-4 text-text-main font-semibold">${section.name}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${section.department_name || '-'}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${section.batch_year_start} - ${section.batch_year_end}</td>
            <td class="px-8 py-4 text-text-main text-center">${section.student_count}</td>
            <td class="px-8 py-4 text-center flex items-center justify-center gap-2">
                <button onclick="editSection(${section.id})" class="text-blue-400 hover:text-blue-300 transition-colors" title="Edit">
                    <i class="fa-solid fa-pen"></i>
                </button>
                <button onclick="deleteSection(${section.id})" class="text-red-400 hover:text-red-300 transition-colors" title="Delete">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

let editingSectionId = null;

function editSection(id) {
    const section = sectionsData.find(s => s.id === id);
    if (!section) return;

    editingSectionId = id;
    document.getElementById('section-name').value = section.name || '';
    document.getElementById('section-dept').value = section.department_id || '';
    document.getElementById('section-start').value = section.batch_year_start || '';
    document.getElementById('section-end').value = section.batch_year_end || '';
    document.getElementById('section-count').value = section.student_count || '';

    toggleModal('modal-section', true);
}

async function saveSection() {
    const name = document.getElementById('section-name').value;
    const department_id = document.getElementById('section-dept').value;
    const batch_year_start = document.getElementById('section-start').value;
    const batch_year_end = document.getElementById('section-end').value;
    const student_count = document.getElementById('section-count').value;

    if (!name || !department_id || !batch_year_start || !batch_year_end || !student_count) {
        return alert('Please fill in all fields');
    }

    try {
        const url = editingSectionId ? `${API_BASE}/sections/${editingSectionId}` : `${API_BASE}/sections/`;
        const method = editingSectionId ? 'PUT' : 'POST';

        const response = await authFetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, department_id: parseInt(department_id), batch_year_start: parseInt(batch_year_start), batch_year_end: parseInt(batch_year_end), student_count: parseInt(student_count) })
        });

        if (response.ok) {
            toggleModal('modal-section', false);
            document.getElementById('section-name').value = '';
            document.getElementById('section-dept').value = '';
            document.getElementById('section-start').value = '';
            document.getElementById('section-end').value = '';
            document.getElementById('section-count').value = '';
            editingSectionId = null;
            loadSections();
        } else {
            const data = await response.json();
            alert(data.detail || data.error || 'Failed to save section');
        }
    } catch (error) {
        console.error('Error saving section:', error);
        alert('Error saving section');
    }
}

async function deleteSection(id) {
    if (!confirm('Are you sure you want to delete this section?')) return;

    try {
        const response = await authFetch(`${API_BASE}/sections/${id}`, { method: 'DELETE' });
        if (response.ok) {
            loadSections();
        }
    } catch (error) {
        console.error('Error deleting section:', error);
    }
}

// --- INIT ---
window.onload = () => {
    renderFaculty();
    renderStudents();
    renderRooms();
    loadInstitution();
    loadTimetable(false);
    updateStats();
    renderConflicts(); // Init conflicts
    showPage('overview');
};
