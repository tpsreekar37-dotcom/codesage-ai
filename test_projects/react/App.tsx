import React, { useEffect, useState } from 'react';
export default function App() {
    const [data, setData] = useState(null);
    // Infinite re-render loop smell
    useEffect(() => {
        setData({});
    });
    return <div>React App</div>;
}