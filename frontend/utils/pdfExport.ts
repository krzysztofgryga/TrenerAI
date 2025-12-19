
import { SavedWorkout, Client, ProgressEntry } from '../types';

/**
 * Very basic markdown table to HTML converter to support professional look in PDF.
 */
const markdownToHtml = (content: string) => {
  let html = content.replace(/\n/g, '<br/>');

  const lines = content.split('\n');
  let inTable = false;
  let tableHtml = '<div class="table-wrapper"><table>';
  let processedLines: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.startsWith('|') && line.endsWith('|')) {
      if (!inTable) {
        inTable = true;
        tableHtml = '<div class="table-wrapper"><table>';
      }
      
      if (line.match(/^[|\-\s:]+$/)) continue;

      const cells = line.split('|').filter(c => c !== '');
      const tag = (tableHtml === '<div class="table-wrapper"><table>') ? 'th' : 'td';
      tableHtml += `<tr>${cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('')}</tr>`;
    } else {
      if (inTable) {
        inTable = false;
        tableHtml += '</table></div>';
        processedLines.push(tableHtml);
      }
      processedLines.push(line);
    }
  }
  
  if (inTable) {
    tableHtml += '</table></div>';
    processedLines.push(tableHtml);
  }

  return processedLines.join('<br/>').replace(/(<br\/>)+<div class="table-wrapper">/g, '<div class="table-wrapper">');
};

export const exportToPDF = (item: SavedWorkout) => {
  const printWindow = window.open('', '_blank');
  if (!printWindow) return;

  const contentHtml = markdownToHtml(item.content);

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>${item.title}</title>
      <script src="https://cdn.tailwindcss.com"></script>
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        body { font-family: 'Inter', sans-serif; padding: 50px; color: #1e293b; line-height: 1.6; background: #fff; }
        .header { border-bottom: 3px solid #3b82f6; margin-bottom: 40px; padding-bottom: 15px; display: flex; justify-content: space-between; align-items: flex-end; }
        h1 { color: #0f172a; font-size: 32px; font-weight: 800; margin: 0; letter-spacing: -0.02em; }
        .date { color: #64748b; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; }
        .content { font-size: 15px; color: #334155; }
        .table-wrapper { margin: 30px 0; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
        th, td { border: 1px solid #e2e8f0; padding: 14px; text-align: left; }
        th { background: #f8fafc; font-weight: 700; color: #0f172a; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em; }
        td { font-size: 13px; }
        .footer { margin-top: 60px; text-align: center; color: #94a3b8; font-size: 11px; border-top: 1px solid #f1f5f9; padding-top: 30px; font-weight: 500; }
        @media print {
          @page { margin: 2cm; }
          body { padding: 0; }
        }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>${item.title}</h1>
        <p class="date">${item.date}</p>
      </div>
      <div class="content">
        ${contentHtml}
      </div>
      <div class="footer">
        DOKUMENT WYGENEROWANY PRZEZ COACHOS - TWÓJ PRYWATNY ASYSTENT TRENERA
      </div>
      <script>
        window.onload = () => {
          setTimeout(() => { window.print(); }, 800);
        };
      </script>
    </body>
    </html>
  `;

  printWindow.document.write(html);
  printWindow.document.close();
};

export const exportAllToPDF = (items: SavedWorkout[]) => {
  const printWindow = window.open('', '_blank');
  if (!printWindow) return;

  const workoutsHtml = items.map(item => `
    <div class="workout-section" style="page-break-after: always;">
      <div class="header" style="border-bottom: 3px solid #3b82f6; margin-bottom: 30px; padding-bottom: 15px; display: flex; justify-content: space-between; align-items: flex-end;">
        <h2 style="color: #0f172a; font-size: 26px; font-weight: 800; margin: 0; letter-spacing: -0.02em;">${item.title}</h2>
        <p style="color: #64748b; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; margin: 0;">${item.date}</p>
      </div>
      <div class="content" style="font-size: 14px; color: #334155;">
        ${markdownToHtml(item.content)}
      </div>
    </div>
  `).join('');

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Eksport Zbiorczy - CoachOS</title>
      <script src="https://cdn.tailwindcss.com"></script>
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        body { font-family: 'Inter', sans-serif; padding: 50px; color: #1e293b; line-height: 1.6; background: #fff; }
        .main-header { text-align: center; margin-bottom: 60px; border-bottom: 5px solid #0f172a; padding-bottom: 40px; }
        .main-header h1 { color: #0f172a; font-size: 36px; font-weight: 800; margin: 0; letter-spacing: -0.03em; text-transform: uppercase; }
        .main-header p { color: #64748b; font-size: 14px; margin-top: 10px; font-weight: 500; }
        .workout-section:last-child { page-break-after: auto !important; }
        .table-wrapper { margin: 25px 0; }
        table { width: 100%; border-collapse: collapse; border: 1px solid #e2e8f0; }
        th, td { border: 1px solid #e2e8f0; padding: 12px; text-align: left; }
        th { background: #f8fafc; font-weight: 700; font-size: 11px; color: #0f172a; }
        td { font-size: 13px; }
        @media print {
          @page { margin: 2cm; }
          body { padding: 0; }
        }
      </style>
    </head>
    <body>
      <div class="main-header">
        <h1>Kompletna Dokumentacja Treningowa</h1>
        <p>Zestawienie wybranych planów i analiz przygotowanych przez CoachOS</p>
        <div style="font-size: 11px; color: #94a3b8; margin-top: 15px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em;">
          Ilość planów: ${items.length} &bull; Wygenerowano: ${new Date().toLocaleDateString('pl-PL')}
        </div>
      </div>
      <div class="workouts-container">
        ${workoutsHtml}
      </div>
      <script>
        window.onload = () => {
          setTimeout(() => { window.print(); }, 1200);
        };
      </script>
    </body>
    </html>
  `;

  printWindow.document.write(html);
  printWindow.document.close();
};

export const exportClientReport = (client: Client) => {
  const printWindow = window.open('', '_blank');
  if (!printWindow) return;

  const progressRows = [...(client.progress || [])].reverse().map(p => `
    <tr>
      <td>${p.date}</td>
      <td>${p.weight} kg</td>
      <td>${p.bodyFat ? p.bodyFat + ' %' : '-'}</td>
      <td>${p.waist ? p.waist + ' cm' : '-'}</td>
      <td style="font-style: italic; font-size: 11px;">${p.notes || '-'}</td>
    </tr>
  `).join('');

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Raport Postępów - ${client.name}</title>
      <script src="https://cdn.tailwindcss.com"></script>
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        body { font-family: 'Inter', sans-serif; padding: 50px; color: #1e293b; line-height: 1.6; background: #fff; }
        .header { border-bottom: 4px solid #3b82f6; margin-bottom: 40px; padding-bottom: 20px; }
        h1 { color: #0f172a; font-size: 32px; font-weight: 800; margin: 0; }
        .client-info { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 40px; background: #f8fafc; padding: 25px; border-radius: 15px; }
        .info-label { font-size: 10px; font-weight: 800; text-transform: uppercase; color: #64748b; letter-spacing: 0.1em; }
        .info-value { font-size: 16px; font-weight: 700; color: #1e293b; }
        h2 { font-size: 18px; font-weight: 800; color: #0f172a; margin: 40px 0 20px 0; text-transform: uppercase; letter-spacing: 0.05em; border-left: 4px solid #3b82f6; padding-left: 15px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 40px; }
        th, td { border: 1px solid #e2e8f0; padding: 12px; text-align: left; }
        th { background: #f8fafc; font-size: 11px; font-weight: 800; text-transform: uppercase; color: #64748b; }
        td { font-size: 13px; }
        .footer { margin-top: 60px; text-align: center; color: #94a3b8; font-size: 11px; border-top: 1px solid #f1f5f9; padding-top: 30px; }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>Raport Postępów Podopiecznego</h1>
        <p style="color: #64748b; font-weight: 600; margin-top: 5px;">Wygenerowano: ${new Date().toLocaleDateString('pl-PL')}</p>
      </div>

      <div class="client-info">
        <div>
          <p class="info-label">Imię i Nazwisko</p>
          <p class="info-value">${client.name}</p>
        </div>
        <div>
          <p class="info-label">Cel Strategiczny</p>
          <p class="info-value">${client.goal}</p>
        </div>
        <div>
          <p class="info-label">Wiek / Waga Startowa</p>
          <p class="info-value">${client.age} lat / ${client.weight} kg</p>
        </div>
        <div>
          <p class="info-label">Status Dokumentu</p>
          <p class="info-value">Poufny - CoachOS Engine</p>
        </div>
      </div>

      <h2>Historia Pomiarów</h2>
      <table>
        <thead>
          <tr>
            <th>Data</th>
            <th>Waga</th>
            <th>Body Fat</th>
            <th>Obwód Pasa</th>
            <th>Notatki</th>
          </tr>
        </thead>
        <tbody>
          ${progressRows || '<tr><td colspan="5" style="text-align: center; color: #94a3b8;">Brak zarejestrowanych pomiarów.</td></tr>'}
        </tbody>
      </table>

      <h2>Notatki i Zalecenia</h2>
      <div style="background: #fff; border: 1px solid #e2e8f0; padding: 25px; border-radius: 15px; min-height: 100px; color: #475569; font-size: 14px;">
        ${client.notes || 'Brak dodatkowych uwag w systemie.'}
      </div>

      <div class="footer">
        DOKUMENT WYGENEROWANY PRZEZ COACHOS - TWÓJ PRYWATNY ASYSTENT TRENERA
      </div>
      <script>
        window.onload = () => { setTimeout(() => { window.print(); }, 800); };
      </script>
    </body>
    </html>
  `;

  printWindow.document.write(html);
  printWindow.document.close();
};
