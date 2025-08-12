
# Coast FI Calculator — Zizzi Investments (No Hidden Files Package)

This package avoids hidden files while you prepare your GitHub repo. 
You'll manually create the Streamlit theme file on GitHub using the contents below.

## Files included
- `streamlit_app.py`
- `requirements.txt`
- `streamlit_theme/config.toml`  ← copy/paste this into GitHub as `.streamlit/config.toml`

## Deploy steps (GitHub + Streamlit Cloud)

1) Create a new **public** GitHub repository (e.g., `coast-fi-calculator`).
2) Upload these files from this ZIP:
   - `streamlit_app.py`
   - `requirements.txt`
3) In your GitHub repo, click **Add file → Create new file** and name it: `.streamlit/config.toml`
4) Open `streamlit_theme/config.toml` from this ZIP and **copy its contents** into the new GitHub file, then **Commit**.

### (Optional) If you prefer folders instead of creating a single file:
- In GitHub, click **Add file → Create new file** and type the path: `.streamlit/config.toml`
- Paste the contents of `streamlit_theme/config.toml` and Commit. GitHub will create the folder structure for you.

5) Go to **Streamlit Community Cloud** and deploy:
   - Repo: your new repo
   - Entry point: `streamlit_app.py`
   - It will build using `requirements.txt`

## WordPress Embed
After deployment, embed your Streamlit URL in a Custom HTML block:
```html
<iframe 
  src="YOUR_STREAMLIT_APP_URL?embed=true" 
  width="100%" 
  height="1100" 
  frameborder="0" 
  scrolling="yes"
  allow="clipboard-read; clipboard-write">
</iframe>
```

## Theme
The theme settings you paste into `.streamlit/config.toml`:
```toml
[theme]
primaryColor="#2F2A26"
backgroundColor="#FFFFFF"
secondaryBackgroundColor="#F7F5F2"
textColor="#111111"
font="sans serif"
```
You can tweak colors later if you have exact hex codes from your brand guide.
