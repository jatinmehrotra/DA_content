import express, { type Express, type Request, type Response } from 'express';
import { todoRouter } from './todo.routes';
import { errorHandler, notFoundHandler } from './error-middleware';

// Build the Express application. Kept separate from the server bootstrap so
// tests can import the app without opening a listening socket.
export function createApp(): Express {
  const app = express();

  app.use(express.json());

  app.get('/health', (_req: Request, res: Response) => {
    res.status(200).json({ status: 'ok' });
  });

  app.use('/todos', todoRouter);

  // 404 for anything unmatched, then the JSON error handler last.
  app.use(notFoundHandler);
  app.use(errorHandler);

  return app;
}
