from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "apps" / "sut" / "frontend" / "src"

router = ROOT / "router.js"
text = router.read_text(encoding="utf-8")
if "/skill-docs" not in text:
    anchor = "  { path: '/users',"
    add = (
        "  { path: '/skill-docs', component: () => import('./views/ai/SkillsDocsView.vue'), "
        "meta: { title: 'Skills 手册' } },\n"
    )
    text = text.replace(anchor, add + anchor, 1)
    router.write_text(text, encoding="utf-8")
    print("router ok")
else:
    print("router already")

app = ROOT / "App.vue"
body = app.read_text(encoding="utf-8")
if "/skill-docs" not in body:
    anchor = "          { to: '/users', icon: 'users', label: '用户管理' },"
    add = (
        anchor
        + "\n          { to: '/skill-docs', icon: 'kb', label: 'Skills 手册' },"
    )
    body = body.replace(anchor, add, 1)
    app.write_text(body, encoding="utf-8")
    print("nav ok")
else:
    print("nav already")
