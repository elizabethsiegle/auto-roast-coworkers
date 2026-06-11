const express = require('express')
const path = require('path')
const { createProxyMiddleware } = require('http-proxy-middleware')

const app = express()
const PORT = process.env.PORT || 3000
const API_URL = process.env.API_URL || 'http://localhost:8000'

app.use('/api', createProxyMiddleware({ target: API_URL, changeOrigin: true }))
app.use(express.static(path.join(__dirname, '../frontend/dist')))
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/dist/index.html'))
})

app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`))
