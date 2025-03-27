import { Router } from 'express';
import { loginUser } from '../controllers/authController';

const router = Router();

router.post('/login', (req, res) => {
  loginUser(req, res);
});

export default router;