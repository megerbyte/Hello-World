#!/usr/bin/env python3
"""
QUESTIONNAIRE Enhanced Freeplane Mind Map to HTML Converter - FINAL CLEAN VERSION

This version creates a questionnaire system with Yes/No buttons that reveal
child nodes based on user selections. Clean interface with no debug console
or answer trail popup.

Author: AI Assistant
Version: 3.0 - FINAL CLEAN QUESTIONNAIRE
"""

import os
import sys
import subprocess
import xml.etree.ElementTree as ET
import re
from pathlib import Path
import shutil
import logging
from html import escape
import base64

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.expanduser('~'), 'freeplane_converter.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CleanFreeplaneConverter:
    def __init__(self):
        self.freeplane_path = self.find_freeplane_installation()
        self.xslt_path = os.path.join(self.freeplane_path, "resources", "xslt", "tohtml.xsl")
        self.java_path = self.find_java()
        
    def find_freeplane_installation(self):
        """Find Freeplane installation directory"""
        possible_paths = [
            "C:\\Program Files\\Freeplane",
            "C:\\Program Files (x86)\\Freeplane",
            os.path.expanduser("~\\AppData\\Local\\Freeplane"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found Freeplane installation at: {path}")
                return path
        
        raise FileNotFoundError("Freeplane installation not found. Please ensure Freeplane is installed.")
    
    def find_java(self):
        """Find Java executable"""
        java_paths = [
            "java",
            "C:\\Program Files\\Java\\jre*\\bin\\java.exe",
            "C:\\Program Files (x86)\\Java\\jre*\\bin\\java.exe",
        ]
        
        try:
            result = subprocess.run(["java", "-version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Found Java in system PATH")
                return "java"
        except FileNotFoundError:
            pass
        
        import glob
        for pattern in java_paths[1:]:
            matches = glob.glob(pattern)
            if matches:
                java_path = matches[0]
                logger.info(f"Found Java at: {java_path}")
                return java_path
        
        raise FileNotFoundError("Java not found. Please ensure Java is installed and accessible.")
    
    def clean_nbsp_characters(self, file_path):
        """Clean nbsp characters from .mm file and save as temporary file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Replace various forms of nbsp
            content = re.sub(r'&nbsp;', '&#160;', content)
            content = re.sub(r'\u00A0', '&#160;', content)
            
            temp_file = file_path + '.temp'
            with open(temp_file, 'w', encoding='utf-8') as file:
                file.write(content)
            
            logger.info(f"Cleaned nbsp characters in: {file_path}")
            return temp_file
            
        except Exception as e:
            logger.error(f"Error cleaning file {file_path}: {str(e)}")
            return None
    
    def parse_richcontent(self, richcontent_element):
        """Parse richcontent element and extract HTML"""
        if richcontent_element is None:
            return ""
        
        logger.debug(f"Parsing richcontent: {ET.tostring(richcontent_element, encoding='unicode')[:200]}...")
        
        html_content = ""
        
        # Method 1: Look for HTML structure
        html_elem = richcontent_element.find('.//html')
        if html_elem is not None:
            # Try to get body content first
            body_elem = html_elem.find('.//body')
            if body_elem is not None:
                # Get all content inside body
                body_content = ET.tostring(body_elem, encoding='unicode', method='html')
                # Remove body tags but keep content
                body_content = re.sub(r'^<body[^>]*>', '', body_content)
                body_content = re.sub(r'</body>\s*$', '', body_content)
                html_content = body_content.strip()
            else:
                # No body, get all HTML content
                html_content = ET.tostring(html_elem, encoding='unicode', method='html')
                # Remove html tags
                html_content = re.sub(r'^<html[^>]*>', '', html_content)
                html_content = re.sub(r'</html>\s*$', '', html_content)
                # Remove head section if present
                html_content = re.sub(r'<head>.*?</head>', '', html_content, flags=re.DOTALL)
                html_content = html_content.strip()
        
        # Method 2: If no HTML structure, look for direct text content
        if not html_content:
            # Check for direct text in richcontent
            if richcontent_element.text and richcontent_element.text.strip():
                html_content = escape(richcontent_element.text.strip())
            else:
                # Get all text content from child elements
                all_text = []
                for elem in richcontent_element.iter():
                    if elem.text:
                        all_text.append(elem.text.strip())
                    if elem.tail:
                        all_text.append(elem.tail.strip())
                
                if all_text:
                    html_content = ' '.join(filter(None, all_text))
                    html_content = escape(html_content)
        
        # Method 3: If still no content, try to serialize the entire element content
        if not html_content:
            try:
                # Get the inner XML content
                inner_content = ET.tostring(richcontent_element, encoding='unicode', method='xml')
                # Remove the richcontent wrapper
                inner_content = re.sub(r'^<richcontent[^>]*>', '', inner_content)
                inner_content = re.sub(r'</richcontent>\s*$', '', inner_content)
                html_content = inner_content.strip()
            except:
                pass
        
        # Clean up the content
        if html_content:
            # Remove extra whitespace
            html_content = re.sub(r'\s+', ' ', html_content)
            # Fix common HTML issues
            html_content = html_content.replace('&amp;', '&')
            html_content = html_content.replace('&lt;', '<')
            html_content = html_content.replace('&gt;', '>')
        
        logger.debug(f"Extracted content: {html_content[:100]}...")
        return html_content
    
    def clean_node_text(self, text):
        """Keep node text as-is (preserve Yes/No prefixes so users can see their answers)"""
        if not text:
            return text
        
        # Keep the original text including Yes/No prefixes
        return text.strip()
    
    def get_node_answer_type(self, original_text):
        """Determine if this node represents a Yes or No answer"""
        if not original_text:
            return None
        
        original_lower = original_text.lower().strip()
        if original_lower.startswith('yes'):
            return 'yes'
        elif original_lower.startswith('no'):
            return 'no'
        return None
    
    def process_node_to_html(self, node, level=0):
        """Convert a node and its children to HTML - CLEAN QUESTIONNAIRE VERSION"""
        html_parts = []
        
        # Get node text
        node_text = node.get('TEXT', '')
        node_id = node.get('ID', f'node_{level}_{id(node)}')
        
        # Check for richcontent in the node (replaces TEXT)
        richcontent_node = node.find('richcontent[@TYPE="NODE"]')
        if richcontent_node is not None:
            rich_text = self.parse_richcontent(richcontent_node)
            if rich_text:
                node_text = rich_text
                logger.debug(f"Using richcontent for node text: {rich_text[:50]}...")
        
        # Store original text and determine answer type
        original_text = node_text
        answer_type = self.get_node_answer_type(original_text)
        
        # Clean the node text (remove Yes/No prefixes)
        cleaned_node_text = self.clean_node_text(node_text)
        
        # Get note content (popup boxes)
        note_content = ""
        
        # Method 1: Standard NOTE type
        richcontent_note = node.find('richcontent[@TYPE="NOTE"]')
        if richcontent_note is not None:
            note_content = self.parse_richcontent(richcontent_note)
            logger.info(f"Found NOTE richcontent for '{cleaned_node_text[:30]}...': {len(note_content)} chars")
        
        # Method 2: Check for other note patterns
        if not note_content:
            for rc in node.findall('richcontent'):
                rc_type = rc.get('TYPE', '').upper()
                if 'NOTE' in rc_type or 'POPUP' in rc_type:
                    note_content = self.parse_richcontent(rc)
                    logger.info(f"Found alternative note type '{rc_type}' for '{cleaned_node_text[:30]}...': {len(note_content)} chars")
                    break
        
        # Get details content
        details_content = ""
        richcontent_details = node.find('richcontent[@TYPE="DETAILS"]')
        if richcontent_details is not None:
            details_content = self.parse_richcontent(richcontent_details)
            logger.info(f"Found DETAILS richcontent for '{cleaned_node_text[:30]}...': {len(details_content)} chars")
        
        # Create the HTML structure
        indent = "  " * level
        
        if level == 0:
            # Root node - show title and first-level buttons only
            html_parts.append('<div class="root-node">')
            if cleaned_node_text:
                html_parts.append(f'  <h1>{cleaned_node_text}</h1>')
            
            # Process child nodes but add buttons at root level
            child_nodes = node.findall('node')
            if child_nodes:
                # Add Yes/No buttons at root level for first question
                html_parts.append('  <div class="root-question-buttons">')
                html_parts.append(f'    <button class="yes-button" data-node-id="root">Yes</button>')
                html_parts.append(f'    <button class="no-button" data-node-id="root">No</button>')
                html_parts.append('  </div>')
                
                # Add hidden container for first-level children
                html_parts.append('  <ul class="root-children" data-parent-id="root">')
                
                for child in child_nodes:
                    child_html = self.process_node_to_html(child, level + 1)
                    html_parts.extend(child_html)
                
                html_parts.append('  </ul>')
            
            html_parts.append('</div>')
            
        else:
            # Regular nodes - add answer type as data attribute
            answer_attr = f' data-answer-type="{answer_type}"' if answer_type else ''
            html_parts.append(f'{indent}<li class="node-level-{level}" id="{node_id}"{answer_attr}>')
            
            # Create a container for the node content
            html_parts.append(f'{indent}  <div class="node-container">')
            
            # Main node content with inline buttons and popup if present
            if cleaned_node_text:
                # Check if this node has children (needs Yes/No buttons)
                child_nodes = node.findall('node')
                
                if note_content:
                    # Add note-content inside node-text and make node-text the trigger
                    html_parts.append(f'{indent}    <div class="node-text note-trigger" data-original-text="{escape(original_text)}">')
                    html_parts.append(f'{indent}      <span class="question-text">{cleaned_node_text}</span>')
                    
                    # Add inline Yes/No buttons at end of question (if has children)
                    if child_nodes:
                        html_parts.append(f'{indent}      <span class="inline-buttons">')
                        html_parts.append(f'{indent}        <button class="yes-button tiny" data-node-id="{node_id}">Yes</button>')
                        html_parts.append(f'{indent}        <button class="no-button tiny" data-node-id="{node_id}">No</button>')
                        html_parts.append(f'{indent}      </span>')
                    
                    html_parts.append(f'{indent}      <div class="note-content">{note_content}</div>')
                    html_parts.append(f'{indent}    </div>')
                else:
                    html_parts.append(f'{indent}    <div class="node-text" data-original-text="{escape(original_text)}">')
                    html_parts.append(f'{indent}      <span class="question-text">{cleaned_node_text}</span>')
                    
                    # Add inline Yes/No buttons at end of question (if has children)
                    if child_nodes:
                        html_parts.append(f'{indent}      <span class="inline-buttons">')
                        html_parts.append(f'{indent}        <button class="yes-button tiny" data-node-id="{node_id}">Yes</button>')
                        html_parts.append(f'{indent}        <button class="no-button tiny" data-node-id="{node_id}">No</button>')
                        html_parts.append(f'{indent}      </span>')
                    
                    html_parts.append(f'{indent}    </div>')
                
                # Add simple text input box under each question
                html_parts.append(f'{indent}    <div class="question-comment">')
                html_parts.append(f'{indent}      <input type="text" class="comment-textbox" placeholder="Leave comments or questions here" size="50" id="textbox-{node_id}">')
                html_parts.append(f'{indent}    </div>')
            
            # Add details if present
            if details_content:
                logger.info(f"Adding details for '{cleaned_node_text[:30]}...'")
                html_parts.append(f'{indent}    <div class="details-content">{details_content}</div>')
            
            html_parts.append(f'{indent}  </div>')
            
            # Process child nodes (buttons are now inline with question text)
            child_nodes = node.findall('node')
            if child_nodes:
                html_parts.append(f'{indent}  <ul class="child-nodes" data-parent-id="{node_id}">')
                
                for child in child_nodes:
                    child_html = self.process_node_to_html(child, level + 1)
                    html_parts.extend(child_html)
                
                html_parts.append(f'{indent}  </ul>')
            
            html_parts.append(f'{indent}</li>')
        
        return html_parts
    
    def convert_mm_to_html_enhanced(self, mm_file_path, output_dir):
        """Convert .mm file to HTML with enhanced richcontent support"""
        try:
            logger.info(f"Converting {mm_file_path}...")
            
            # Clean the file first
            cleaned_file = self.clean_nbsp_characters(mm_file_path)
            if not cleaned_file:
                return False
            
            # Parse the XML
            tree = ET.parse(cleaned_file)
            root = tree.getroot()
            
            if root.tag != 'map':
                logger.error(f"File {mm_file_path} is not a valid mind map")
                os.remove(cleaned_file)
                return False
            
            # Get the root node
            root_node = root.find('node')
            if root_node is None:
                logger.error(f"No root node found in {mm_file_path}")
                os.remove(cleaned_file)
                return False
            
            # Debug: Count richcontent elements
            all_richcontent = root.findall('.//richcontent')
            note_richcontent = root.findall('.//richcontent[@TYPE="NOTE"]')
            logger.info(f"Found {len(all_richcontent)} total richcontent elements, {len(note_richcontent)} are NOTEs")
            
            # Convert to HTML
            html_content = self.process_node_to_html(root_node)
            
            # Create complete HTML document
            mm_filename = os.path.splitext(os.path.basename(mm_file_path))[0]
            html_file_path = os.path.join(output_dir, f"{mm_filename}.html")
            
            full_html = self.create_complete_html(html_content, mm_filename)
            
            with open(html_file_path, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
            # Clean up temporary file
            os.remove(cleaned_file)
            
            logger.info(f"Successfully converted with rich content: {mm_file_path} -> {html_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error converting {mm_file_path}: {str(e)}")
            import traceback
            traceback.print_exc()
            if 'cleaned_file' in locals() and os.path.exists(cleaned_file):
                os.remove(cleaned_file)
            return False
    
    def create_complete_html(self, content_lines, title):
        """Create a complete HTML document with clean styling - NO DEBUG, NO TRAIL"""
        content = '\n'.join(content_lines)
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)}</title>
    <style>
/* CLEAN QUESTIONNAIRE - Enhanced Freeplane HTML Export Styles */
body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f8f9fa;
    line-height: 1.6;
}}

#mindmap-container {{
    max-width: 1200px;
    margin: 0 auto;
    background-color: white;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}}

.root-node h1 {{
    text-align: center;
    color: #2c3e50;
    border-bottom: 3px solid #3498db;
    padding-bottom: 10px;
    margin-bottom: 30px;
}}

ul {{
    list-style: none;
    padding-left: 0;
    margin: 10px 0;
}}

ul ul {{
    padding-left: 30px;
    border-left: 2px solid #ecf0f1;
    margin-left: 10px;
}}

li {{
    margin: 8px 0;
    position: relative;
}}

/* QUESTIONNAIRE: Hide ALL child nodes by default */
.root-children {{
    display: none !important;
}}

.child-nodes {{
    display: none !important;
}}

/* Show selected nodes */
.root-children.revealed {{
    display: block !important;
}}

.child-nodes.revealed {{
    display: block !important;
}}

/* Hide non-matching answer nodes */
li.hidden-answer {{
    display: none !important;
}}

.node-container {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    flex-wrap: wrap;
}}

.node-text {{
    padding: 8px 12px;
    background-color: #ecf0f1;
    border-radius: 6px;
    border-left: 4px solid #3498db;
    margin-bottom: 5px;
    flex: 1;
    min-width: 200px;
    position: relative;
    cursor: default;
}}

.node-level-1 .node-text {{
    background-color: #e8f4fd;
    border-left-color: #2980b9;
    font-weight: bold;
    font-size: 18px;
}}

.node-level-2 .node-text {{
    background-color: #f0f8f0;
    border-left-color: #27ae60;
    font-size: 16px;
}}

.node-level-3 .node-text {{
    background-color: #fef9e7;
    border-left-color: #f39c12;
    font-size: 14px;
}}

.node-level-4 .node-text {{
    background-color: #fdf2f2;
    border-left-color: #e74c3c;
    font-size: 14px;
}}

/* ROOT QUESTION BUTTONS - Special styling for root level */
.root-question-buttons {{
    margin: 20px 0;
    display: flex;
    gap: 20px;
    justify-content: center;
    padding: 20px;
    background-color: #f8f9fa;
    border-radius: 10px;
    border: 2px dashed #dee2e6;
}}

/* QUESTIONNAIRE BUTTONS */
.question-buttons {{
    margin: 10px 0;
    display: flex;
    gap: 15px;
    justify-content: flex-start;
}}

.yes-button, .no-button {{
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
    min-width: 100px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* Root level buttons - larger */
.root-question-buttons .yes-button,
.root-question-buttons .no-button {{
    padding: 16px 32px;
    font-size: 18px;
    min-width: 120px;
}}

.yes-button {{
    background-color: #28a745;
    color: white;
    box-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
}}

.yes-button:hover {{
    background-color: #218838;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(40, 167, 69, 0.4);
}}

.no-button {{
    background-color: #dc3545;
    color: white;
    box-shadow: 0 2px 4px rgba(220, 53, 69, 0.3);
}}

.no-button:hover {{
    background-color: #c82333;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(220, 53, 69, 0.4);
}}

.yes-button:active, .no-button:active {{
    transform: translateY(0);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}}

/* Selected button states */
.yes-button.selected {{
    background-color: #155724;
    box-shadow: 0 0 0 3px rgba(40, 167, 69, 0.5);
    transform: scale(1.05);
}}

.no-button.selected {{
    background-color: #721c24;
    box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.5);
    transform: scale(1.05);
}}

/* Inline button container */
.inline-buttons {{
    display: inline-flex;
    gap: 5px;
    margin-left: 10px;
    align-items: center;
}}

/* Tiny buttons - 75% smaller (25% of original size) */
.yes-button.tiny, .no-button.tiny {{
    padding: 3px 6px;
    font-size: 10px;
    min-width: 25px;
    border-radius: 4px;
    font-weight: normal;
    letter-spacing: 0;
    text-transform: none;
}}

/* Comment button */
.comment-btn {{
    background: #6c757d;
    color: white;
    border: none;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    font-size: 12px;
    cursor: pointer;
    margin-left: 8px;
    transition: all 0.2s ease;
}}

.comment-btn:hover {{
    background: #5a6268;
    transform: scale(1.1);
}}

.comment-btn.has-comment {{
    background: #28a745;
}}

.comment-btn.has-comment:hover {{
    background: #1e7e34;
}}

/* Comment box styles */
.comment-box {{
    display: none;
    margin-top: 10px;
    padding: 15px;
    background-color: #f8f9fa;
    border: 2px solid #dee2e6;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}}

.comment-box.show {{
    display: block;
    animation: slideDown 0.3s ease-out;
}}

@keyframes slideDown {{
    from {{
        opacity: 0;
        transform: translateY(-10px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

.comment-input {{
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-family: inherit;
    font-size: 14px;
    resize: vertical;
    min-height: 60px;
}}

.comment-actions {{
    margin-top: 10px;
    display: flex;
    gap: 10px;
}}

.save-comment, .cancel-comment {{
    padding: 6px 12px;
    border: none;
    border-radius: 4px;
    font-size: 12px;
    cursor: pointer;
    transition: background-color 0.2s ease;
}}

.save-comment {{
    background-color: #28a745;
    color: white;
}}

.save-comment:hover {{
    background-color: #218838;
}}

.cancel-comment {{
    background-color: #6c757d;
    color: white;
}}

.cancel-comment:hover {{
    background-color: #5a6268;
}}

.saved-comment {{
    margin-top: 10px;
    padding: 8px 12px;
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 4px;
    font-size: 14px;
    display: none;
}}

.saved-comment.show {{
    display: block;
}}

/* Simple comment textbox under each question */
.question-comment {{
    margin-top: 8px;
    margin-bottom: 10px;
}}

.comment-textbox {{
    width: 100%;
    max-width: 400px;
    padding: 6px 10px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-family: inherit;
    font-size: 14px;
    background-color: #f8f9fa;
    transition: border-color 0.2s ease, background-color 0.2s ease;
}}

.comment-textbox:focus {{
    outline: none;
    border-color: #3498db;
    background-color: white;
    box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}}

.comment-textbox::placeholder {{
    color: #6c757d;
    font-style: italic;
}}

/* Note Popup Styles - MOUSE-OVER TO SHOW POPUP */
.node-text.note-trigger {{
    background-color: #fff3cd !important;
    border-left-color: #ffc107 !important;
    cursor: help;
}}

.node-text.note-trigger:hover {{
    background-color: #ffeaa7 !important;
}}

.note-content {{
    display: none;
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    min-width: 300px;
    max-width: 500px;
    background-color: #fff3cd;
    border: 2px solid #ffc107;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
    z-index: 1000;
    font-size: 14px;
    line-height: 1.5;
    animation: fadeIn 0.3s ease-in-out;
}}

@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateX(-50%) translateY(-10px); }}
    to {{ opacity: 1; transform: translateX(-50%) translateY(0); }}
}}

.note-content::before {{
    content: '';
    position: absolute;
    top: -10px;
    left: 50%;
    transform: translateX(-50%);
    width: 0;
    height: 0;
    border-left: 10px solid transparent;
    border-right: 10px solid transparent;
    border-bottom: 10px solid #ffc107;
}}

/* MOUSE-OVER: Show note on hover */
.node-text.note-trigger:hover .note-content {{
    display: block !important;
}}

/* Details Content */
.details-content {{
    margin-top: 8px;
    padding: 10px;
    background-color: #f8f9fa;
    border-radius: 4px;
    border-left: 3px solid #6c757d;
    font-size: 14px;
    color: #495057;
    width: 100%;
}}

/* Mobile support */
@media (max-width: 768px) {{
    .root-question-buttons,
    .question-buttons {{
        flex-direction: column;
        gap: 10px;
    }}
    
    .yes-button, .no-button {{
        width: 100%;
    }}
}}
    </style>
</head>
<body>
    <div id="mindmap-container">
        {content}
    </div>
    
    <script>
// CLEAN QUESTIONNAIRE - Enhanced Mindmap JavaScript (NO DEBUG, NO TRAIL)

document.addEventListener('DOMContentLoaded', function() {{
    try {{
        // Initialize questionnaire functionality
        initializeQuestionnaire();
        
        // Initialize note popups (MOUSE-OVER)
        initializeNotePopups();
        
    }} catch (error) {{
        console.error('Initialization error:', error);
    }}
}});

function initializeQuestionnaire() {{
    // Find all Yes/No buttons
    const yesButtons = document.querySelectorAll('.yes-button');
    const noButtons = document.querySelectorAll('.no-button');
    
    // Add click handlers for Yes buttons
    yesButtons.forEach((button, index) => {{
        const nodeId = button.getAttribute('data-node-id');
        
        button.addEventListener('click', function(e) {{
            e.preventDefault();
            e.stopPropagation();
            
            handleQuestionAnswer(nodeId, 'Yes', button);
        }});
    }});
    
    // Add click handlers for No buttons
    noButtons.forEach((button, index) => {{
        const nodeId = button.getAttribute('data-node-id');
        
        button.addEventListener('click', function(e) {{
            e.preventDefault();
            e.stopPropagation();
            
            handleQuestionAnswer(nodeId, 'No', button);
        }});
    }});
}}

function handleQuestionAnswer(nodeId, answer, clickedButton) {{
    // Mark the clicked button as selected
    const buttonContainer = clickedButton.parentElement;
    const allButtons = buttonContainer.querySelectorAll('button');
    allButtons.forEach(btn => btn.classList.remove('selected'));
    clickedButton.classList.add('selected');
    
    // Find and show the appropriate child nodes
    const childNodesContainer = document.querySelector(`ul[data-parent-id="${{nodeId}}"]`);
    if (childNodesContainer) {{
        // Get all direct child list items
        const childItems = childNodesContainer.querySelectorAll(':scope > li');
        
        let visibleCount = 0;
        
        childItems.forEach((childItem, index) => {{
            const answerType = childItem.getAttribute('data-answer-type');
            
            if (answerType === answer.toLowerCase()) {{
                childItem.classList.remove('hidden-answer');
                childItem.style.display = 'block';
                visibleCount++;
                
                // Reset any nested child containers
                const nestedChildContainers = childItem.querySelectorAll('.child-nodes');
                nestedChildContainers.forEach(container => {{
                    container.style.display = 'none';
                    container.classList.remove('revealed');
                }});
                
            }} else {{
                childItem.classList.add('hidden-answer');
                childItem.style.display = 'none';
            }}
        }});
        
        // Show the child nodes container
        childNodesContainer.classList.add('revealed');
        childNodesContainer.style.display = 'block';
        
        // CONTINUOUS FLOW: Smooth scroll to new questions
        if (visibleCount > 0) {{
            setTimeout(() => {{
                const firstVisibleChild = childNodesContainer.querySelector('li:not(.hidden-answer)');
                if (firstVisibleChild) {{
                    firstVisibleChild.scrollIntoView({{ 
                        behavior: 'smooth', 
                        block: 'center' 
                    }});
                }}
            }}, 300);
        }}
    }}
}}

function initializeNotePopups() {{
    const noteTriggers = document.querySelectorAll('.node-text.note-trigger');
    
    noteTriggers.forEach((trigger, index) => {{
        const content = trigger.querySelector('.note-content');
        
        if (content) {{
            // MOUSE-OVER handlers
            trigger.addEventListener('mouseenter', function(e) {{
                content.style.display = 'block';
            }});
            
            trigger.addEventListener('mouseleave', function(e) {{
                content.style.display = 'none';
            }});
            
            // Mobile touch support
            trigger.addEventListener('touchstart', function(e) {{
                if (content.style.display === 'block') {{
                    content.style.display = 'none';
                }} else {{
                    document.querySelectorAll('.note-content').forEach(otherContent => {{
                        if (otherContent !== content) {{
                            otherContent.style.display = 'none';
                        }}
                    }});
                    content.style.display = 'block';
                }}
                e.preventDefault();
                e.stopPropagation();
            }});
            
            // Prevent popup from disappearing when hovering over it
            content.addEventListener('mouseenter', function(e) {{
                content.style.display = 'block';
            }});
            
            content.addEventListener('mouseleave', function(e) {{
                content.style.display = 'none';
            }});
        }}
    }});
}}

// Comment system functions
function toggleComment(nodeId) {{
    const commentBox = document.getElementById(`comment-${{nodeId}}`);
    const commentBtn = document.querySelector(`button[onclick="toggleComment('${{nodeId}}')"]`);
    
    if (commentBox.classList.contains('show')) {{
        commentBox.classList.remove('show');
    }} else {{
        // Hide all other comment boxes
        document.querySelectorAll('.comment-box.show').forEach(box => {{
            box.classList.remove('show');
        }});
        
        commentBox.classList.add('show');
        
        // Focus on the textarea
        const textarea = commentBox.querySelector('.comment-input');
        setTimeout(() => textarea.focus(), 100);
    }}
}}

function saveComment(nodeId) {{
    const commentBox = document.getElementById(`comment-${{nodeId}}`);
    const textarea = commentBox.querySelector('.comment-input');
    const savedDiv = document.getElementById(`saved-${{nodeId}}`);
    const commentBtn = document.querySelector(`button[onclick="toggleComment('${{nodeId}}')"]`);
    
    const commentText = textarea.value.trim();
    
    if (commentText) {{
        // Save to localStorage
        const comments = JSON.parse(localStorage.getItem('mindmapComments') || '{{}}');
        comments[nodeId] = commentText;
        localStorage.setItem('mindmapComments', JSON.stringify(comments));
        
        // Show saved comment
        savedDiv.innerHTML = `<strong>Your comment:</strong> ${{commentText}}`;
        savedDiv.classList.add('show');
        
        // Update button appearance
        commentBtn.classList.add('has-comment');
        
        // Hide comment box
        commentBox.classList.remove('show');
        
        // Clear textarea
        textarea.value = '';
    }}
}}

function cancelComment(nodeId) {{
    const commentBox = document.getElementById(`comment-${{nodeId}}`);
    const textarea = commentBox.querySelector('.comment-input');
    
    // Clear textarea and hide box
    textarea.value = '';
    commentBox.classList.remove('show');
}}

function loadStoredComments() {{
    const comments = JSON.parse(localStorage.getItem('mindmapComments') || '{{}}');
    const textboxComments = JSON.parse(localStorage.getItem('mindmapTextboxComments') || '{{}}');
    
    // Load old-style comments (if any exist)
    Object.keys(comments).forEach(nodeId => {{
        const savedDiv = document.getElementById(`saved-${{nodeId}}`);
        const commentBtn = document.querySelector(`button[onclick="toggleComment('${{nodeId}}')"]`);
        
        if (savedDiv && commentBtn) {{
            savedDiv.innerHTML = `<strong>Your comment:</strong> ${{comments[nodeId]}}`;
            savedDiv.classList.add('show');
            commentBtn.classList.add('has-comment');
        }}
    }});
    
    // Load textbox comments
    Object.keys(textboxComments).forEach(nodeId => {{
        const textbox = document.getElementById(`textbox-${{nodeId}}`);
        if (textbox) {{
            textbox.value = textboxComments[nodeId];
        }}
    }});
}}

function saveTextboxComment(nodeId, value) {{
    const textboxComments = JSON.parse(localStorage.getItem('mindmapTextboxComments') || '{{}}');
    
    if (value.trim()) {{
        textboxComments[nodeId] = value.trim();
    }} else {{
        delete textboxComments[nodeId];
    }}
    
    localStorage.setItem('mindmapTextboxComments', JSON.stringify(textboxComments));
}}

function initializeTextboxes() {{
    const textboxes = document.querySelectorAll('.comment-textbox');
    
    textboxes.forEach(textbox => {{
        const nodeId = textbox.id.replace('textbox-', '');
        
        // Save on blur (when user clicks away)
        textbox.addEventListener('blur', function() {{
            saveTextboxComment(nodeId, textbox.value);
        }});
        
        // Save on Enter key
        textbox.addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{
                saveTextboxComment(nodeId, textbox.value);
                textbox.blur(); // Remove focus
            }}
        }});
        
        // Auto-save every 2 seconds while typing
        let saveTimeout;
        textbox.addEventListener('input', function() {{
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(() => {{
                saveTextboxComment(nodeId, textbox.value);
            }}, 2000);
        }});
    }});
}}

// Initialize comment system
document.addEventListener('DOMContentLoaded', function() {{
    loadStoredComments();
    initializeTextboxes();
}});
    </script>
</body>
</html>"""
        
        return html_template
    
    def create_output_folder(self, mm_file_path):
        """Create output folder for the HTML file"""
        mm_dir = os.path.dirname(mm_file_path)
        mm_filename = os.path.splitext(os.path.basename(mm_file_path))[0]
        output_dir = os.path.join(mm_dir, mm_filename)
        
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")
        
        return output_dir
    
    def process_directory(self, start_dir):
        """Process all .mm files in directory tree"""
        start_path = Path(start_dir)
        if not start_path.exists():
            logger.error(f"Directory does not exist: {start_dir}")
            return
        
        logger.info(f"Starting CLEAN QUESTIONNAIRE processing of directory: {start_dir}")
        
        mm_files = list(start_path.rglob("*.mm"))
        
        if not mm_files:
            logger.warning(f"No .mm files found in {start_dir}")
            return
        
        logger.info(f"Found {len(mm_files)} .mm files to process")
        
        success_count = 0
        error_count = 0
        
        for mm_file in mm_files:
            try:
                logger.info(f"Processing: {mm_file}")
                
                output_dir = self.create_output_folder(str(mm_file))
                
                # Convert to HTML with rich content support
                if self.convert_mm_to_html_enhanced(str(mm_file), output_dir):
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing {mm_file}: {str(e)}")
                error_count += 1
        
        logger.info(f"CLEAN QUESTIONNAIRE processing complete. Success: {success_count}, Errors: {error_count}")

def main():
    """Main function with interactive file/directory input"""
    print("=" * 70)
    print("ENHANCED QUESTIONNAIRE Freeplane Mind Map to HTML Converter")
    print("Version 4.1 - With Simple Text Input & Preserved Yes/No Answers")
    print("=" * 70)
    
    try:
        converter = CleanFreeplaneConverter()
        
        while True:
            input_path = input("\nEnter the path to your .mm file or directory: ").strip()
            
            if not input_path:
                print("Please enter a valid path.")
                continue
            
            input_path = input_path.strip('"\'')
            
            if os.path.exists(input_path):
                break
            else:
                print(f"Path does not exist: {input_path}")
                retry = input("Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    return
        
        # Ask for output directory
        output_dir = input("Enter output directory (press Enter for 'html_output'): ").strip().strip('"\'')
        if not output_dir:
            output_dir = "html_output"
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        if os.path.isfile(input_path):
            # Single file
            if input_path.endswith('.mm'):
                print(f"\nConverting: {input_path}")
                success = converter.convert_mm_to_html_enhanced(input_path, output_dir)
                if success:
                    print("✓ Successfully converted!")
                else:
                    print("✗ Conversion failed!")
            else:
                print("Error: Input file must have .mm extension")
                return
        elif os.path.isdir(input_path):
            # Directory
            converter.process_directory(input_path)
        
        print("\n" + "=" * 50)
        print("ENHANCED QUESTIONNAIRE conversion process completed!")
        print("Features included:")
        print("✓ Rich content (HTML formatting)")
        print("✓ Simple text input boxes under each question")
        print("✓ Popups triggered by MOUSE-OVER (hover)")
        print("✓ Details sections")
        print("✓ Clean interface")
        print("✓ Responsive design")
        print("✓ Enhanced styling")
        print("✓ PRESERVED: Yes/No prefixes show user's previous answers")
        print("✓ QUESTIONNAIRE: Tiny Yes/No buttons at end of questions")
        print("✓ CONTINUOUS FLOW: Questionnaire continues through multiple levels")
        print("✓ AUTO-SCROLL: Smooth scrolling to new questions")
        print("✓ AUTO-SAVE: Text input automatically saved as you type")
        print("=" * 50)
        print("Usage:")
        print("• HOVER over yellow nodes to see popup notes")
        print("• CLICK tiny Yes/No buttons at end of questions to navigate")
        print("• TYPE in text boxes under questions to leave comments")
        print("• Text is automatically saved as you type or press Enter")
        print("• All comments persist in browser storage")
        print("• Questionnaire continues through multiple levels automatically")
        print("• Clean interface with smooth scrolling")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"An error occurred: {str(e)}")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()