module.exports = {
  useNavigate: () => jest.fn(),
  BrowserRouter: ({ children }) => children,
  Route: ({ children }) => children,
  Routes: ({ children }) => children,
  Link: ({ children, to }) => children,
};
