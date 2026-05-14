export class ExportConverter {
    /**
     * Convert HTML to Markdown format
     */
    static htmlToMarkdown(html) {
        let md = html;
        // Remove style tags and their content
        md = md.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
        // Convert headers
        md = md.replace(/<h1[^>]*>(.*?)<\/h1>/gi, '\n# $1\n');
        md = md.replace(/<h2[^>]*>(.*?)<\/h2>/gi, '\n## $1\n');
        md = md.replace(/<h3[^>]*>(.*?)<\/h3>/gi, '\n### $1\n');
        md = md.replace(/<h4[^>]*>(.*?)<\/h4>/gi, '\n#### $1\n');
        md = md.replace(/<h5[^>]*>(.*?)<\/h5>/gi, '\n##### $1\n');
        md = md.replace(/<h6[^>]*>(.*?)<\/h6>/gi, '\n###### $1\n');
        // Convert bold and italic
        md = md.replace(/<strong[^>]*>(.*?)<\/strong>/gi, '**$1**');
        md = md.replace(/<b[^>]*>(.*?)<\/b>/gi, '**$1**');
        md = md.replace(/<em[^>]*>(.*?)<\/em>/gi, '*$1*');
        md = md.replace(/<i[^>]*>(.*?)<\/i>/gi, '*$1*');
        // Convert links
        md = md.replace(/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/gi, '[$2]($1)');
        // Convert line breaks and paragraphs
        md = md.replace(/<br\s*\/?>/gi, '\n');
        md = md.replace(/<p[^>]*>/gi, '\n\n');
        md = md.replace(/<\/p>/gi, '');
        // Convert lists
        md = md.replace(/<ul[^>]*>/gi, '\n');
        md = md.replace(/<\/ul>/gi, '\n');
        md = md.replace(/<ol[^>]*>/gi, '\n');
        md = md.replace(/<\/ol>/gi, '\n');
        md = md.replace(/<li[^>]*>(.*?)<\/li>/gi, (match, content) => {
            return `\n* ${content.trim()}`;
        });
        // Convert code blocks
        md = md.replace(/<pre[^>]*><code[^>]*>([\s\S]*?)<\/code><\/pre>/gi, '\n```\n$1\n```\n');
        md = md.replace(/<code[^>]*>(.*?)<\/code>/gi, '`$1`');
        // Convert blockquotes
        md = md.replace(/<blockquote[^>]*>(.*?)<\/blockquote>/gi, '\n> $1\n');
        // Convert tables - basic support
        md = md.replace(/<table[^>]*>/gi, '\n');
        md = md.replace(/<\/table>/gi, '\n');
        md = md.replace(/<thead[^>]*>/gi, '');
        md = md.replace(/<\/thead>/gi, '');
        md = md.replace(/<tbody[^>]*>/gi, '');
        md = md.replace(/<\/tbody>/gi, '');
        md = md.replace(/<tr[^>]*>/gi, '\n|');
        md = md.replace(/<\/tr>/gi, '|');
        md = md.replace(/<th[^>]*>(.*?)<\/th>/gi, ' $1 |');
        md = md.replace(/<td[^>]*>(.*?)<\/td>/gi, ' $1 |');
        // Remove remaining HTML tags
        md = md.replace(/<div[^>]*>/gi, '\n');
        md = md.replace(/<\/div>/gi, '');
        md = md.replace(/<span[^>]*>/gi, '');
        md = md.replace(/<\/span>/gi, '');
        md = md.replace(/<[^>]+>/g, '');
        // Clean up entities
        md = md.replace(/&nbsp;/g, ' ');
        md = md.replace(/&lt;/g, '<');
        md = md.replace(/&gt;/g, '>');
        md = md.replace(/&amp;/g, '&');
        md = md.replace(/&quot;/g, '"');
        md = md.replace(/&#39;/g, "'");
        // Clean up excessive whitespace
        md = md.replace(/\n{4,}/g, '\n\n\n');
        md = md.replace(/^\s+$/gm, '');
        return md.trim();
    }
    /**
     * Process images in HTML content
     */
    static async processImages(html, client, embedImages = true) {
        const imgRegex = /<img[^>]*src="([^"]+)"[^>]*>/g;
        const images = [];
        let match;
        let processedHtml = html;
        while ((match = imgRegex.exec(html)) !== null) {
            images.push({
                tag: match[0],
                url: match[1],
                size: 0,
            });
        }
        if (!embedImages) {
            return {
                html: processedHtml,
                images: images.map((img) => ({ url: img.url, size: img.size })),
            };
        }
        // Download and embed images
        for (const img of images) {
            try {
                let imageUrl = img.url;
                // Security: Only process images from the same Atlassian domain or relative paths.
                // This is to prevent SSRF attacks where the server could be forced to make requests
                // to arbitrary internal or external services.
                if (imageUrl.startsWith('http')) {
                    try {
                        const url = new URL(imageUrl);
                        const clientBaseUrl = new URL(client.defaults.baseURL);
                        if (url.hostname !== clientBaseUrl.hostname) {
                            console.error(`Skipping external image from different domain: ${imageUrl}`);
                            continue; // Skip images from other domains
                        }
                        // Use only the path and query for same-domain URLs
                        imageUrl = url.pathname + url.search;
                    }
                    catch (e) {
                        console.error(`Invalid image URL: ${imageUrl}`, e);
                        continue; // Skip invalid URLs
                    }
                }
                else if (!imageUrl.startsWith('/')) {
                    // Ensure relative URLs are handled correctly, assuming they are relative to the domain root
                    imageUrl = '/' + imageUrl;
                }
                // Download image
                const response = await client.get(imageUrl, {
                    responseType: 'arraybuffer',
                    timeout: 30000,
                });
                if (response.status === 200 && response.data) {
                    let mimeType = response.headers['content-type'] || 'image/png';
                    if (!mimeType.startsWith('image/')) {
                        if (imageUrl.includes('.png'))
                            mimeType = 'image/png';
                        else if (imageUrl.includes('.jpg') || imageUrl.includes('.jpeg'))
                            mimeType = 'image/jpeg';
                        else if (imageUrl.includes('.gif'))
                            mimeType = 'image/gif';
                        else if (imageUrl.includes('.svg'))
                            mimeType = 'image/svg+xml';
                        else
                            mimeType = 'image/png';
                    }
                    const base64Data = Buffer.from(response.data).toString('base64');
                    const dataUri = `data:${mimeType};base64,${base64Data}`;
                    // Replace image src with data URI
                    const newImgTag = img.tag.replace(img.url, dataUri);
                    processedHtml = processedHtml.replace(img.tag, newImgTag);
                    img.base64 = base64Data;
                    img.size = response.data.byteLength;
                }
            }
            catch (error) {
                console.error(`Failed to process image ${img.url}:`, error);
            }
        }
        return {
            html: processedHtml,
            images: images.map((img) => ({
                url: img.url,
                base64: img.base64,
                size: img.size,
            })),
        };
    }
    /**
     * Prepare clean HTML for export
     */
    static prepareHtmlForExport(htmlContent, title, includeStyles = false) {
        const css = includeStyles
            ? `
      <style>
        @page { size: A4; margin: 2cm; }
        @media print {
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        }
        
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
          font-size: 11pt;
          line-height: 1.6;
          color: #333;
          max-width: 210mm;
          margin: 0 auto;
          padding: 20px;
        }
        
        h1, h2, h3, h4, h5, h6 {
          margin-top: 1.5em;
          margin-bottom: 0.5em;
          font-weight: 600;
          page-break-after: avoid;
        }
        
        h1 { font-size: 24pt; }
        h2 { font-size: 18pt; }
        h3 { font-size: 14pt; }
        h4 { font-size: 12pt; }
        
        p { margin-bottom: 1em; }
        
        ul, ol { margin: 1em 0; padding-left: 2em; }
        li { margin-bottom: 0.5em; }
        
        table {
          width: 100%;
          border-collapse: collapse;
          margin: 1em 0;
          page-break-inside: auto;
        }
        
        th, td {
          border: 1px solid #ddd;
          padding: 8px;
          text-align: left;
        }
        
        th { background: #f5f5f5; font-weight: 600; }
        
        img {
          max-width: 100%;
          height: auto;
          display: block;
          margin: 1em auto;
          page-break-inside: avoid;
        }
        
        code {
          background: #f5f5f5;
          padding: 2px 4px;
          font-family: monospace;
          font-size: 90%;
        }
        
        pre {
          background: #f5f5f5;
          padding: 1em;
          overflow-x: auto;
          margin: 1em 0;
          page-break-inside: avoid;
        }
        
        blockquote {
          border-left: 4px solid #ddd;
          padding-left: 1em;
          margin: 1em 0;
          color: #666;
        }
      </style>
    `
            : '';
        return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  ${css}
</head>
<body>
  ${htmlContent}
</body>
</html>`;
    }
    /**
     * Create Markdown document with metadata
     */
    static createMarkdownDocument(content, metadata) {
        const frontMatter = `---
title: ${metadata.title}
${metadata.space ? `space: ${metadata.space}${metadata.spaceKey ? ` (${metadata.spaceKey})` : ''}` : ''}
${metadata.version ? `version: ${metadata.version}` : ''}
${metadata.modified ? `modified: ${metadata.modified.toISOString()}` : ''}
exported: ${new Date().toISOString()}
${metadata.sourceUrl ? `source: ${metadata.sourceUrl}` : ''}
---

# ${metadata.title}

${metadata.space ? `> **Space:** ${metadata.space}  ` : ''}
${metadata.modified ? `> **Last Modified:** ${metadata.modified.toLocaleDateString()}  ` : ''}
${metadata.version ? `> **Version:** ${metadata.version}  ` : ''}
> **Exported:** ${new Date().toLocaleDateString()}

---

${content}

---

## Export Information

- **Page ID:** ${metadata.pageId}
- **Export Date:** ${new Date().toLocaleString()}
${metadata.sourceUrl ? `- **Source URL:** ${metadata.sourceUrl}` : ''}
`;
        return frontMatter;
    }
}
//# sourceMappingURL=export-converter.js.map