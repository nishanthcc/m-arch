export function setupRoutes(app: any) {
    app.post('/api/charge', (req, res) => res.json({ ok: true }));
}
