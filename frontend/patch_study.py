import re

filepath = r"src\app\study-360\[subjectId]\page.tsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add state variables for escalations and queries
content = content.replace(
    "const [excl, setExcl] = useState<any[]>([]);",
    "const [excl, setExcl] = useState<any[]>([]);\n  const [monitorHistory, setMonitorHistory] = useState<any[]>([]);"
)

# 2. Add API calls
content = content.replace(
    "saeRes, teaeRes, exclRes\n        ] = await Promise.allSettled([",
    "saeRes, teaeRes, exclRes, escRes, qRes\n        ] = await Promise.allSettled(["
)

content = content.replace(
    "api.get(`/analysis/exclusion_violations?cut=${currentCut}`)\n        ]);",
    "api.get(`/analysis/exclusion_violations?cut=${currentCut}`),\n          api.get(`/stage2/escalations`),\n          api.get(`/stage2/queries`)\n        ]);"
)

# 3. Process API responses
process_str = """
        const exclEv = extractEv(exclRes).filter((e: any) => e.USUBJID === subjectId);
"""

replacement_str = """
        const exclEv = extractEv(exclRes).filter((e: any) => e.USUBJID === subjectId);

        const subjEscalations = escRes.status === 'fulfilled' ? escRes.value.data.filter((e: any) => e.usubjid === subjectId) : [];
        const subjQueries = qRes.status === 'fulfilled' ? qRes.value.data.filter((q: any) => q.usubjid === subjectId) : [];
        
        subjEscalations.forEach((esc: any) => {
            events.push({
                id: `esc-${esc.id}`,
                type: 'Stage 2 Escalation',
                date: "2099-12-31", // Sort to end or top depending
                title: `Escalation: ${esc.code}`,
                description: `Status: ${esc.status} | Monitor: ${esc.monitor_decision || 'Pending'} | ${esc.summary}`,
                icon: <ShieldAlert size={14} className="text-amber-500" />,
                evidence: esc.evidence
            });
        });
        
        subjQueries.forEach((q: any) => {
            events.push({
                id: `q-${q.id}`,
                type: 'Stage 2 Query',
                date: "2099-12-31",
                title: `Data Query`,
                description: `Status: ${q.status} | ${q.text}`,
                icon: <FileWarning size={14} className="text-blue-500" />,
                evidence: q.evidence
            });
        });
"""

content = content.replace(process_str, replacement_str)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
