export class SimplePdfExport {
    /**
     * Generate a print-ready HTML document from Confluence content
     */
    static generatePrintableHtml(content, title, baseUrl, metadata) {
        // Professional CSS for print-ready document
        const css = `
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        @page {
          size: A4;
          margin: 2cm;
        }
        
        @media print {
          body {
            print-color-adjust: exact;
            -webkit-print-color-adjust: exact;
          }
        }
        
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        
        body {
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
          font-size: 11pt;
          line-height: 1.6;
          color: #24292e;
          background: white;
          max-width: 210mm;
          margin: 0 auto;
          padding: 20px;
        }
        
        /* Header */
        .document-header {
          border-bottom: 3px solid #0052CC;
          padding-bottom: 20px;
          margin-bottom: 30px;
        }
        
        .document-title {
          font-size: 24pt;
          font-weight: 700;
          color: #172B4D;
          margin-bottom: 10px;
        }
        
        .document-meta {
          font-size: 10pt;
          color: #6B778C;
          display: flex;
          gap: 20px;
        }
        
        .meta-item {
          display: flex;
          align-items: center;
          gap: 5px;
        }
        
        /* Content */
        .document-content {
          color: #172B4D;
        }
        
        h1, h2, h3, h4, h5, h6 {
          margin-top: 24px;
          margin-bottom: 12px;
          font-weight: 600;
          color: #172B4D;
          page-break-after: avoid;
        }
        
        h1 {
          font-size: 20pt;
          border-bottom: 2px solid #DFE1E6;
          padding-bottom: 8px;
        }
        
        h2 {
          font-size: 16pt;
          margin-top: 30px;
        }
        
        h3 {
          font-size: 14pt;
        }
        
        h4 {
          font-size: 12pt;
        }
        
        p {
          margin-bottom: 12px;
          text-align: justify;
        }
        
        /* Lists */
        ul, ol {
          margin: 12px 0;
          padding-left: 30px;
        }
        
        li {
          margin-bottom: 6px;
        }
        
        /* Code */
        code {
          background: #F4F5F7;
          padding: 2px 6px;
          border-radius: 3px;
          font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
          font-size: 10pt;
          color: #FF5630;
        }
        
        pre {
          background: #F4F5F7;
          border: 1px solid #DFE1E6;
          border-radius: 3px;
          padding: 12px;
          overflow-x: auto;
          margin: 16px 0;
          page-break-inside: avoid;
        }
        
        pre code {
          background: none;
          padding: 0;
          color: #172B4D;
        }
        
        /* Tables */
        table {
          width: 100%;
          border-collapse: collapse;
          margin: 16px 0;
          font-size: 10pt;
          page-break-inside: auto;
        }
        
        th {
          background: #F4F5F7;
          font-weight: 600;
          text-align: left;
          padding: 10px;
          border: 1px solid #DFE1E6;
        }
        
        td {
          padding: 10px;
          border: 1px solid #DFE1E6;
        }
        
        tr:nth-child(even) {
          background: #FAFBFC;
        }
        
        /* Images */
        img {
          max-width: 100%;
          height: auto;
          display: block;
          margin: 16px auto;
          page-break-inside: avoid;
        }
        
        /* Blockquotes */
        blockquote {
          border-left: 4px solid #0052CC;
          padding-left: 16px;
          margin: 16px 0;
          color: #5E6C84;
          font-style: italic;
        }
        
        /* Links */
        a {
          color: #0052CC;
          text-decoration: none;
        }
        
        a:hover {
          text-decoration: underline;
        }
        
        /* Confluence macros */
        .panel, .confluence-information-macro {
          border: 1px solid #DFE1E6;
          border-radius: 3px;
          padding: 12px;
          margin: 16px 0;
          background: #F4F5F7;
        }
        
        .panel-heading {
          font-weight: 600;
          margin-bottom: 8px;
        }
        
        .confluence-information-macro-icon {
          display: none;
        }
        
        /* Footer */
        .document-footer {
          margin-top: 50px;
          padding-top: 20px;
          border-top: 1px solid #DFE1E6;
          font-size: 9pt;
          color: #6B778C;
          text-align: center;
        }
        
        /* Page breaks */
        .page-break {
          page-break-after: always;
        }
        
        @media screen {
          body {
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            margin: 20px auto;
            background: white;
          }
          
          .document-wrapper {
            min-height: 297mm;
          }
        }
      </style>
    `;
        // Clean and process content
        let processedContent = content;
        // Remove Confluence-specific classes that might break styling
        processedContent = processedContent.replace(/class="[^"]*"/g, '');
        // Fix relative URLs
        processedContent = processedContent
            .replace(/src="\/wiki\//g, `src="${baseUrl}/wiki/`)
            .replace(/href="\/wiki\//g, `href="${baseUrl}/wiki/`);
        // Build the HTML document
        const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  ${css}
</head>
<body>
  <div class="document-wrapper">
    <div class="document-header">
      <h1 class="document-title">${title}</h1>
      <div class="document-meta">
        ${metadata?.space ? `<div class="meta-item">📁 Space: ${metadata.space}</div>` : ''}
        ${metadata?.author ? `<div class="meta-item">👤 Author: ${metadata.author}</div>` : ''}
        ${metadata?.lastModified ? `<div class="meta-item">📅 Modified: ${metadata.lastModified}</div>` : ''}
        <div class="meta-item">📄 Exported: ${new Date().toLocaleDateString()}</div>
      </div>
    </div>
    
    <div class="document-content">
      ${processedContent}
    </div>
    
    <div class="document-footer">
      <p>Exported from Confluence | ${baseUrl}</p>
      <p>Generated on ${new Date().toLocaleString()}</p>
    </div>
  </div>
</body>
</html>`;
        return html;
    }
}
//# sourceMappingURL=simple-pdf-export.js.map