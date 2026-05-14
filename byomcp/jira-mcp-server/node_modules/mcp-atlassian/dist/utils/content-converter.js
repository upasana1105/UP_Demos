/**
 * Simple content converter between Markdown and Confluence Storage Format
 * This is a basic implementation - for production use, consider using
 * a library like @atlaskit/editor-markdown-transformer
 */
import { sanitizeHtml } from './html-sanitizer.js';
export class ContentConverter {
    /**
     * Convert Markdown to Confluence Storage Format (XHTML)
     * This is a simplified converter for basic formatting
     */
    static markdownToStorage(markdown) {
        let html = markdown;
        // Convert headers
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
        // Convert bold and italic
        html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        html = html.replace(/_(.+?)_/g, '<em>$1</em>');
        // Convert code blocks
        html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            const language = lang || 'none';
            return `<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">${language}</ac:parameter><ac:plain-text-body><![CDATA[${code.trim()}]]></ac:plain-text-body></ac:structured-macro>`;
        });
        // Convert inline code
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        // Convert links
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
        // Convert unordered lists
        html = html.replace(/^\* (.+)$/gim, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        // Convert ordered lists
        html = html.replace(/^\d+\. (.+)$/gim, '<li>$1</li>');
        // Convert line breaks to paragraphs
        const lines = html.split('\n');
        const processedLines = [];
        let inList = false;
        let inCodeBlock = false;
        for (const line of lines) {
            if (line.includes('<ac:structured-macro')) {
                inCodeBlock = true;
            }
            if (line.includes('</ac:structured-macro>')) {
                inCodeBlock = false;
            }
            if (line.startsWith('<ul>') || line.startsWith('<ol>')) {
                inList = true;
            }
            if (line.includes('</ul>') || line.includes('</ol>')) {
                inList = false;
            }
            if (line.trim() &&
                !inList &&
                !inCodeBlock &&
                !line.startsWith('<h') &&
                !line.startsWith('<ac:') &&
                !line.startsWith('<ul') &&
                !line.startsWith('<ol')) {
                processedLines.push(`<p>${line}</p>`);
            }
            else {
                processedLines.push(line);
            }
        }
        return processedLines.join('\n');
    }
    /**
     * Convert Confluence Storage Format to Markdown
     * This is a simplified converter for basic formatting
     */
    static storageToMarkdown(storage) {
        // First, sanitize the HTML to prevent any script injection from affecting the conversion
        const sanitizedStorage = sanitizeHtml(storage);
        let markdown = sanitizedStorage;
        // Convert headers
        markdown = markdown.replace(/<h1>(.*?)<\/h1>/gi, '# $1');
        markdown = markdown.replace(/<h2>(.*?)<\/h2>/gi, '## $1');
        markdown = markdown.replace(/<h3>(.*?)<\/h3>/gi, '### $1');
        markdown = markdown.replace(/<h4>(.*?)<\/h4>/gi, '#### $1');
        markdown = markdown.replace(/<h5>(.*?)<\/h5>/gi, '##### $1');
        markdown = markdown.replace(/<h6>(.*?)<\/h6>/gi, '###### $1');
        // Convert bold and italic
        markdown = markdown.replace(/<strong><em>(.*?)<\/em><\/strong>/gi, '***$1***');
        markdown = markdown.replace(/<em><strong>(.*?)<\/strong><\/em>/gi, '***$1***');
        markdown = markdown.replace(/<strong>(.*?)<\/strong>/gi, '**$1**');
        markdown = markdown.replace(/<em>(.*?)<\/em>/gi, '*$1*');
        markdown = markdown.replace(/<b>(.*?)<\/b>/gi, '**$1**');
        markdown = markdown.replace(/<i>(.*?)<\/i>/gi, '*$1*');
        // Convert code blocks
        markdown = markdown.replace(/<ac:structured-macro ac:name="code">.*?<ac:parameter ac:name="language">(.*?)<\/ac:parameter>.*?<ac:plain-text-body><!\[CDATA\[([\s\S]*?)\]\]><\/ac:plain-text-body>.*?<\/ac:structured-macro>/gi, (match, lang, code) => {
            return `\`\`\`${lang}\n${code}\n\`\`\``;
        });
        // Convert inline code
        markdown = markdown.replace(/<code>(.*?)<\/code>/gi, '`$1`');
        // Convert links
        markdown = markdown.replace(/<a href="(.*?)">(.*?)<\/a>/gi, '[$2]($1)');
        // Convert lists
        markdown = markdown.replace(/<ul>([\s\S]*?)<\/ul>/gi, (match, content) => {
            return content.replace(/<li>(.*?)<\/li>/gi, '* $1');
        });
        markdown = markdown.replace(/<ol>([\s\S]*?)<\/ol>/gi, (match, content) => {
            let counter = 1;
            return content.replace(/<li>(.*?)<\/li>/gi, () => {
                return `${counter++}. $1`;
            });
        });
        // Convert paragraphs
        markdown = markdown.replace(/<p>(.*?)<\/p>/gi, '$1\n');
        // Convert line breaks
        markdown = markdown.replace(/<br\s*\/?>/gi, '\n');
        // Remove remaining HTML tags
        markdown = markdown.replace(/<[^>]*>/g, '');
        // Clean up extra whitespace
        markdown = markdown.replace(/\n{3,}/g, '\n\n');
        return markdown.trim();
    }
    /**
     * Detect if content is already in storage format
     */
    static isStorageFormat(content) {
        // This check is now just a hint for conversion, not for security.
        return (content.includes('<') &&
            (content.includes('<p>') ||
                content.includes('<h1>') ||
                content.includes('<h2>') ||
                content.includes('<h3>') ||
                content.includes('<ac:') ||
                content.includes('<ul>') ||
                content.includes('<ol>')));
    }
    /**
     * Auto-detect format, convert if needed, and ALWAYS sanitize.
     * This function is a critical security control. It ensures that any content,
     * whether it's user-provided HTML or Markdown, is passed through the HTML sanitizer
     * before being sent to the Confluence API. This prevents XSS attacks.
     */
    static ensureStorageFormat(content) {
        let html;
        if (this.isStorageFormat(content)) {
            html = content;
        }
        else {
            html = this.markdownToStorage(content);
        }
        // Sanitize the HTML output to prevent XSS attacks. This is the critical security step.
        return sanitizeHtml(html);
    }
}
//# sourceMappingURL=content-converter.js.map