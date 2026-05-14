import DOMPurify from 'dompurify';
import { JSDOM } from 'jsdom';
// Create a JSDOM window to be used by DOMPurify in the Node.js environment
// This is necessary because DOMPurify requires a DOM to parse and sanitize HTML.
const window = new JSDOM('').window;
const dompurify = DOMPurify(window);
/**
 * Configuration for DOMPurify.
 * This configuration is designed to be permissive enough to allow common Confluence formatting,
 * while still protecting against XSS attacks.
 * It explicitly allows certain tags and attributes that are known to be used by Confluence.
 */
const SANITIZE_CONFIG = {
    // Allow a broad range of tags commonly used in Confluence
    ALLOWED_TAGS: [
        'h1',
        'h2',
        'h3',
        'h4',
        'h5',
        'h6',
        'p',
        'br',
        'hr',
        'strong',
        'b',
        'em',
        'i',
        'u',
        's',
        'strike',
        'del',
        'sub',
        'sup',
        'ul',
        'ol',
        'li',
        'a',
        'img',
        'code',
        'pre',
        'blockquote',
        'table',
        'thead',
        'tbody',
        'tfoot',
        'tr',
        'th',
        'td',
        'div',
        'span',
        // Confluence-specific macros/elements (as custom tags)
        'ac:structured-macro',
        'ac:plain-text-body',
        'ac:parameter',
        'ac:link',
        'ac:image',
        'ri:page',
        'ri:attachment',
    ],
    // Allow a broad range of attributes
    ALLOWED_ATTR: [
        'href',
        'src',
        'alt',
        'title',
        'class',
        'style',
        'id',
        'width',
        'height',
        'align',
        'data-attachment-type',
        'data-attachment-name',
        'data-macro-name',
        'ac:name',
        'ac:schema-version',
        'ri:content-title',
        'ri:version-at-save',
    ],
    // Forbid dangerous tags explicitly, even if they were somehow allowed
    FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed', 'form'],
    // Forbid dangerous attributes
    FORBID_ATTR: [
        'onerror',
        'onload',
        'onclick',
        'onmouseover',
        'onfocus',
        'onblur',
        'autofocus',
        'formaction',
    ],
    // Allow data attributes
    ALLOW_DATA_ATTR: true,
    // Keep the content of tags that are not allowed
    KEEP_CONTENT: true,
};
/**
 * Sanitizes an HTML string to prevent XSS attacks.
 * It uses a DOMPurify instance configured with a safe list of tags and attributes.
 *
 * @param dirtyHtml The potentially unsafe HTML string to sanitize.
 * @returns The sanitized HTML string.
 */
export function sanitizeHtml(dirtyHtml) {
    return dompurify.sanitize(dirtyHtml, SANITIZE_CONFIG);
}
//# sourceMappingURL=html-sanitizer.js.map