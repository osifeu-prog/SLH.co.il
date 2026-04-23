import { Pool } from "pg";

const pool = new Pool({ connectionString: process.env.DATABASE_URL });

export default async function handler(req, res) {
  if (req.method === "GET") {
    try {
      const result = await pool.query("SELECT * FROM feedback ORDER BY id DESC LIMIT 20");
      res.status(200).json(result.rows);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  } else {
    res.status(405).end();
  }
}
