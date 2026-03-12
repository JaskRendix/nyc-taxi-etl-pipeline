import express from 'express'
import { PrismaClient } from '@prisma/client'

const app = express()
const prisma = new PrismaClient()

app.get('/api/stats', async (_req, res) => {
  try {
    const stats = await prisma.yellowCabCleaned.aggregate({
      _avg: { fare_amount: true },
      _count: { id: true }
    })

    res.json({
      avgFare: stats._avg.fare_amount,
      tripCount: stats._count.id
    })
  } catch (err) {
    console.error(err)
    res.status(500).json({ error: 'Internal server error' })
  }
})

app.listen(3001, () => console.log('🚀 API running on http://localhost:3001'))
