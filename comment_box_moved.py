<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Minimal Mind Map with Comment Boxes</title>
  <style>
    body {
      font-family: sans-serif;
      padding: 20px;
      background: #f9f9f9;
    }
    .node {
      margin-left: 20px;
      margin-top: 10px;
      padding: 10px;
      background: #fff;
      border: 1px solid #ccc;
      border-radius: 8px;
      box-shadow: 1px 1px 4px rgba(0,0,0,0.1);
    }
    .node-title {
      font-weight: bold;
      margin-bottom: 4px;
      color: #333;
    }
    .comment-box {
      margin-top: 12px;
      padding-top: 8px;
      border-top: 1px solid #eee;
    }
    .comment-input {
      width: 100%;
      max-width: 50ch;
      resize: vertical;
      font-size: 14px;
      padding: 8px;
      border: 1px solid #ddd;
      border-radius: 4px;
      box-sizing: border-box;
    }
    .comment-label {
      font-size: 12px;
      color: #666;
      margin-bottom: 4px;
      font-style: italic;
    }
  </style>
</head>
<body>
  <h1>Example Mind Map</h1>

  <!-- Root Node -->
  <div class="node" id="node-root">
    <div class="node-title">Is the defendant a minor?</div>
    <div class="comment-box" id="comment-root">
      <div class="comment-label">Comments for: Is the defendant a minor?</div>
      <textarea class="comment-input" placeholder="Leave comments and questions here." rows="3" cols="50"></textarea>
    </div>

    <!-- Yes Child -->
    <div class="node" id="node-yes">
      <div class="node-title">Yes: Proceed to juvenile assessment.</div>
      <div class="comment-box" id="comment-yes">
        <div class="comment-label">Comments for: Yes - Proceed to juvenile assessment</div>
        <textarea class="comment-input" placeholder="Leave comments and questions here." rows="3" cols="50"></textarea>
      </div>
    </div>

    <!-- No Child -->
    <div class="node" id="node-no">
      <div class="node-title">No: Move to adult criminal process.</div>
      <div class="comment-box" id="comment-no">
        <div class="comment-label">Comments for: No - Move to adult criminal process</div>
        <textarea class="comment-input" placeholder="Leave comments and questions here." rows="3" cols="50"></textarea>
      </div>
    </div>
  </div>

</body>
</html>
