'use client'
import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";

export default function Page() {
  const [reports, setReports] = useState([]);

  useEffect(() => {
    const fetchReports = async () => {
      const response = await fetch('http://localhost:8000/list-reports');
      const data = await response.json();
      setReports(data);
    };

    fetchReports();
  }, []);

  const handleDownload = async (reportId) => {
    const response = await fetch(`http://localhost:8000/get-report/${reportId}`);
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = reportId;
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  return (
    <div>
      <h1>Available Reports</h1>
      <ul>
        {reports.map((report) => (
          <li key={report.report_id}>
            {report.report_filename}
            <Button onClick={() => handleDownload(report.report_id)}>Download</Button>
          </li>
        ))}
      </ul>
    </div>
  );
}