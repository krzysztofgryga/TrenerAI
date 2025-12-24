import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar';
import Home from './pages/Home';
import Workouts from './pages/Workouts';
import AICoach from './pages/AICoach';
import Profile from './pages/Profile';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/workouts" element={<Workouts />} />
          <Route path="/coach" element={<AICoach />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
        <NavBar />
      </div>
    </Router>
  );
}

export default App;
