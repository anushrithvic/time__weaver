// --- DATA LAYER ---
let facultyData = JSON.parse(localStorage.getItem('timeWeaver_faculty')) || [
    { id: 1, name: "Dr. Sarah Thorne", dept: "CS", role: "Professor", subject: "Networks", current: 16, max: 18 },
    { id: 2, name: "Prof. Alan Turing", dept: "CS", role: "Professor", subject: "Algorithms", current: 12, max: 15 }
];

let studentData = JSON.parse(localStorage.getItem('timeWeaver_students')) || [];
let institutionData = JSON.parse(localStorage.getItem('timeWeaver_institution')) || { name: 'TimeWeaver University', year: '2025-2026' };
let roomData = JSON.parse(localStorage.getItem('timeWeaver_rooms')) || [];
let ruleData = JSON.parse(localStorage.getItem('timeWeaver_rules')) || [];
let timetableData = JSON.parse(localStorage.getItem('timeWeaver_timetable')) || [];

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
}

// --- FACULTY LOGIC ---
async function saveFaculty() {
    const name = document.getElementById('fac-name').value;
    const dept = document.getElementById('fac-dept').value;
    const role = document.getElementById('fac-role').value;
    const subject = document.getElementById('fac-subject').value;
    const max = parseInt(document.getElementById('fac-max').value);
    const dob = document.getElementById('fac-dob').value;

    if (!name || !subject || !dob) return alert("Please enter name, subject, and date of birth");

    try {
        const response = await fetch('http://localhost:3000/api/admin/create-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, role: 'faculty', dob })
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Failed to create user credentials');
        }

        const data = await response.json();
        alert(`Faculty User Created!\nUsername: ${data.generatedCredentials.username}\nPassword: ${data.generatedCredentials.password}`);

    } catch (err) {
        console.error(err);
        alert("Error creating login credentials: " + err.message);
        return;
    }

    facultyData.push({
        id: Date.now(),
        name,
        dept,
        role,
        subject,
        current: 0,
        max
    });
    localStorage.setItem('timeWeaver_faculty', JSON.stringify(facultyData));

    toggleModal('modal-faculty', false);
    renderFaculty();
    updateStats();
}

function deleteFaculty(id) {
    facultyData = facultyData.filter(f => f.id !== id);
    localStorage.setItem('timeWeaver_faculty', JSON.stringify(facultyData));
    renderFaculty();
    updateStats();
}

function renderFaculty() {
    const list = document.getElementById('faculty-list');
    if (!list) return;
    list.innerHTML = facultyData.map(f => {
        const isOver = f.current > f.max;
        const percent = Math.min((f.current / f.max) * 100, 100);
        return `
            <tr class="hover:bg-main transition-colors border-b border-border-color last:border-0">
                <td class="px-8 py-5">
                    <div class="font-bold text-text-main">${f.name}</div>
                    <div class="text-xs text-text-muted font-medium">${f.role || 'Faculty'}</div>
                </td>
                <td class="px-8 py-5 text-text-muted text-sm font-medium">${f.dept}</td>
                <td class="px-8 py-5 text-text-muted text-sm font-medium">${f.subject || '-'}</td>
                <td class="px-8 py-5">
                    <div class="flex flex-col items-end">
                        <span class="text-xs font-black mb-2 ${isOver ? 'text-red-400' : 'text-cyan-400'}">${f.current} / ${f.max} HRS</span>
                        <div class="w-48 h-2 bg-main rounded-full overflow-hidden border border-border-color">
                            <div class="h-full ${isOver ? 'bg-red-500 vector-glow-red' : 'bg-cyan-500 vector-glow-cyan'} transition-all duration-1000" style="width: ${percent}%"></div>
                        </div>
                    </div>
                </td>
                <td class="px-8 py-5 text-center">
                    <button onclick="deleteFaculty(${f.id})" class="text-text-muted hover:text-red-400 transition-colors">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// --- STUDENT LOGIC ---
async function saveStudent() {
    const name = document.getElementById('stu-name').value;
    const roll = document.getElementById('stu-roll').value;
    const batch = document.getElementById('stu-batch').value;
    const dept = document.getElementById('stu-dept').value;
    const section = document.getElementById('stu-sec').value;
    const dob = document.getElementById('stu-dob').value;

    if (!name || !roll || !section || !dob) return alert("Please fill all details including DOB");

    try {
        const response = await fetch('http://localhost:3000/api/admin/create-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, role: 'student', dob })
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Failed to create user credentials');
        }

        const data = await response.json();
        alert(`Student User Created!\nUsername: ${data.generatedCredentials.username}\nPassword: ${data.generatedCredentials.password}`);

    } catch (err) {
        console.error(err);
        alert("Error creating login credentials: " + err.message);
        return;
    }

    studentData.push({ id: Date.now(), name, roll, batch, dept, section });
    localStorage.setItem('timeWeaver_students', JSON.stringify(studentData));

    toggleModal('modal-student', false);
    renderStudents();
}

function deleteStudent(id) {
    studentData = studentData.filter(s => s.id !== id);
    localStorage.setItem('timeWeaver_students', JSON.stringify(studentData));
    renderStudents();
}

function renderStudents() {
    const list = document.getElementById('student-list');
    if (!list) return;
    list.innerHTML = studentData.map(s => `
        <tr class="hover:bg-main transition-colors border-b border-border-color last:border-0">
            <td class="px-8 py-5 font-bold text-text-main">${s.name}</td>
            <td class="px-8 py-5 text-text-muted text-sm font-medium">${s.roll}</td>
            <td class="px-8 py-5 text-text-muted text-sm font-medium">${s.dept} - ${s.batch}</td>
            <td class="px-8 py-5 text-text-muted text-sm font-medium">Sec-${s.section}</td>
                <td class="px-8 py-5 text-center">
                <button onclick="deleteStudent(${s.id})" class="text-text-muted hover:text-red-400 transition-colors">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// --- ROOM LOGIC ---
function saveRoom() {
    const building = document.getElementById('room-building').value;
    const number = document.getElementById('room-number').value;
    const type = document.getElementById('room-type').value;
    const capacity = parseInt(document.getElementById('room-capacity').value);

    // Checkboxes
    const hasProjector = document.getElementById('room-projector').checked;
    const hasLab = document.getElementById('room-lab').checked;
    const hasAC = document.getElementById('room-ac').checked;

    if (!building || !number || !capacity) return alert("Please fill required fields (Building, Number, Capacity)");

    const newRoom = {
        id: Date.now(),
        building,
        number,
        fullName: `${building} - ${number}`,
        type,
        capacity,
        features: { hasProjector, hasLab, hasAC }
    };

    roomData.push(newRoom);
    localStorage.setItem('timeWeaver_rooms', JSON.stringify(roomData));

    toggleModal('modal-room', false);
    renderRooms();
}

function deleteRoom(id) {
    roomData = roomData.filter(r => r.id !== id);
    localStorage.setItem('timeWeaver_rooms', JSON.stringify(roomData));
    renderRooms();
}

function renderRooms() {
    const list = document.getElementById('room-list');
    if (!list) return;
    list.innerHTML = roomData.map(r => `
        <tr class="hover:bg-main transition-colors border-b border-border-color last:border-0">
            <td class="px-8 py-5 font-bold text-text-main">${r.fullName}</td>
            <td class="px-8 py-5 text-text-muted text-sm font-medium">
                <span class="bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 px-2 py-1 rounded-md text-xs uppercase font-bold tracking-wider">${r.type}</span>
            </td>
            <td class="px-8 py-5 text-text-muted text-sm font-medium">${r.capacity}</td>
            <td class="px-8 py-5 text-text-muted text-sm font-medium">
                <div class="flex gap-2">
                    ${r.features.hasProjector ? '<i class="fa-solid fa-video text-cyan-500/50" title="Projector"></i>' : ''}
                    ${r.features.hasLab ? '<i class="fa-solid fa-flask text-fuchsia-500/50" title="Lab Equipment"></i>' : ''}
                    ${r.features.hasAC ? '<i class="fa-solid fa-snowflake text-blue-500/50" title="AC"></i>' : ''}
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

function saveRule() {
    const name = document.getElementById('rule-name').value;
    const type = document.getElementById('rule-type').value;
    const weight = document.getElementById('rule-weight').value;
    const desc = document.getElementById('rule-desc').value;
    const isHard = document.getElementById('rule-hard').checked;

    if (!name) return alert("Rule Name is required");

    const newRule = {
        id: Date.now(),
        name,
        type,
        weight,
        description: desc,
        isHard,
        isActive: true
    };

    ruleData.push(newRule);
    localStorage.setItem('timeWeaver_rules', JSON.stringify(ruleData));

    toggleModal('modal-rule', false);
    renderRules();
}

function deleteRule(id) {
    ruleData = ruleData.filter(r => r.id !== id);
    localStorage.setItem('timeWeaver_rules', JSON.stringify(ruleData));
    renderRules();
}

function renderRules() {
    const list = document.getElementById('rule-list');
    if (!list) return;
    list.innerHTML = ruleData.map(r => `
        <div class="bg-main p-4 rounded-xl border border-border-color flex justify-between items-center mb-3 hover:border-text-muted transition-all">
            <div>
                <div class="flex items-center gap-2 mb-1">
                    <h4 class="font-bold text-text-main">${r.name}</h4>
                    ${r.isHard
            ? '<span class="bg-red-500/10 text-red-400 text-[10px] px-2 py-0.5 rounded font-bold uppercase border border-red-500/20">Hard</span>'
            : '<span class="bg-blue-500/10 text-blue-400 text-[10px] px-2 py-0.5 rounded font-bold uppercase border border-blue-500/20">Soft</span>'}
                </div>
                <p class="text-xs text-text-muted">${r.description || 'No description'}</p>
                <div class="mt-2 text-[10px] font-mono text-text-muted bg-card inline-block px-2 py-1 rounded border border-border-color">
                    Type: ${r.type} | Weight: ${r.weight}
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

function updateStats() {
    if (document.getElementById('stat-faculty-count')) {
        document.getElementById('stat-faculty-count').innerText = facultyData.length;
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

function generateTimetable(mode) {
    const criteria = getFilterCriteria();
    const { year, program, dept, sem, section } = criteria;

    if (!confirm(`Are you sure you want to ${mode} the schedule for ${program} ${dept} Sem-${sem} Sec-${section}? This will overwrite existing entries.`)) return;

    // Load existing data
    let allTimetableData = JSON.parse(localStorage.getItem('timeWeaver_timetable')) || [];

    // Remove existing entries for this specific criteria if regenerating
    allTimetableData = allTimetableData.filter(t =>
        !(t.dept === dept && t.sem === sem && t.section === section)
    );

    const times = ["09:00", "10:00", "11:00", "12:00", "01:00", "02:00", "03:00"];
    const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
    const subjects = ["Data Structures", "Algorithms", "Database Systems", "OS", "Networks", "AI/ML", "Cloud Computing"];

    // Generate new entries
    days.forEach(day => {
        times.forEach(time => {
            // Randomly decide if a class exists (e.g., 80% chance)
            if (Math.random() > 0.2) {
                const randomSubject = subjects[Math.floor(Math.random() * subjects.length)];

                // Filter faculty by department availability (simple logic)
                const deptFaculty = facultyData.filter(f => f.dept === dept);
                const assignedFaculty = deptFaculty.length > 0
                    ? deptFaculty[Math.floor(Math.random() * deptFaculty.length)].name
                    : "TBA";

                // Pick a random room if available
                const relevantRooms = roomData.filter(r => r.type === 'classroom');
                const assignedRoom = relevantRooms.length > 0
                    ? relevantRooms[Math.floor(Math.random() * relevantRooms.length)].fullName
                    : "R-" + (100 + parseInt(sem) * 10 + Math.floor(Math.random() * 5));

                allTimetableData.push({
                    id: Date.now() + Math.random(),
                    day: day,
                    time: time,
                    subject: randomSubject,
                    faculty: assignedFaculty,
                    room: assignedRoom,
                    // Meta tags
                    dept: dept,
                    sem: sem,
                    section: section,
                    program: program,
                    year: year
                });
            }
        });
    });

    localStorage.setItem('timeWeaver_timetable', JSON.stringify(allTimetableData));
    alert("Timetable Generated Successfully!");
    loadTimetable(true);
}

function loadTimetable(isFiltered = false) {
    // Updated Times Slots to match provided Real Data
    const times = [
        "08:00 - 08:50", "08:50 - 09:40", "09:40 - 10:30",
        "10:45 - 11:35", "11:35 - 12:25", "12:25 - 01:15",
        "02:05 - 02:55", "02:55 - 03:45", "03:45 - 04:35",
        "04:35 - 05:25", "05:25 - 06:15"
    ];
    const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

    let allData = JSON.parse(localStorage.getItem('timeWeaver_timetable'));

    if (!allData || allData.length === 0) {
        allData = [];
    }

    // FILTER LOGIC
    let displayData = allData;
    if (isFiltered) {
        const criteria = getFilterCriteria();
        displayData = allData.filter(t =>
            t.dept === criteria.dept &&
            t.sem === criteria.sem &&
            t.section === criteria.section
        );
    } else {
        const criteria = getFilterCriteria(); // will take default selected values from DOM
        displayData = allData.filter(t =>
            (t.dept === criteria.dept && t.sem === criteria.sem && t.section === criteria.section) ||
            (!t.section)
        );
    }

    const body = document.getElementById('timetable-body');
    if (!body) return;

    body.innerHTML = times.map(time => `
        <div class="timetable-grid border-b border-border-color">
            <div class="p-6 border-r border-border-color text-xs font-black text-text-muted flex items-center justify-center">${time}</div>
            ${days.map(day => {
        // Find class for this day/time in the filtered set
        const classSession = displayData.find(t => t.day === day && t.time === time);

        return `
                    <div class="p-3 border-r border-border-color h-32 transition-colors hover:bg-main">
                        ${classSession ? `
                            <div class="bg-card border border-border-color p-4 rounded-2xl h-full shadow-sm flex flex-col justify-between group hover:border-cyan-500/50 hover:shadow-lg hover:shadow-cyan-900/20 transition-all">
                                <div>
                                    <p class="text-[9px] font-black text-cyan-400 tracking-tighter uppercase mb-1 neon-text">Lecture</p>
                                    <p class="text-[13px] font-extrabold text-text-main leading-tight">${classSession.subject}</p>
                                    <p class="text-[10px] text-text-muted mt-1 font-semibold">${classSession.faculty}</p>
                                </div>
                                <div class="flex justify-between items-end">
                                    <span class="text-[10px] text-text-muted font-bold">${classSession.room}</span>
                                    <i class="fa-solid fa-circle-check text-green-500 text-xs opacity-0 group-hover:opacity-100 transition-opacity"></i>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                `;
    }).join('')}
        </div>
    `).join('');
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
