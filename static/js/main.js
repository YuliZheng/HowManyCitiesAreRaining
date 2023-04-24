import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// Scene, camera, and renderer setup
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth, window.innerHeight);
document.getElementById('container').appendChild(renderer.domElement);

// Controls for user to rotate the globe
const controls = new OrbitControls(camera, renderer.domElement);
controls.minDistance = 12;
controls.maxDistance = 40;


// Earth geometry and material
const earthGeometry = new THREE.SphereGeometry(10, 64, 64);
const earthTexture = new THREE.TextureLoader().load('../static/earth_texture_map_highres.jpg');
const earthMaterial = new THREE.MeshPhongMaterial({ map: earthTexture });
const earth = new THREE.Mesh(earthGeometry, earthMaterial);
scene.add(earth);

// Rotate the earth to focus on the desired location
// const targetLatitude = 30; // Modify the latitude value as needed
// const targetLongitude = 110; // Modify the longitude value as needed

// earth.rotation.y = -targetLongitude * (Math.PI / 180);
// earth.rotation.x = targetLatitude * (Math.PI / 180);


// Light source
const ambientLight = new THREE.AmbientLight(0xffffff, 1);
scene.add(ambientLight);

camera.position.z = 20;


const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
window.addEventListener('mousemove', onMouseMove, false);
function onMouseMove(event) {
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObject(earth);

    if (intersects.length > 0) {
        const intersectPoint = intersects[0].point;
        earth.worldToLocal(intersectPoint); // 转换为局部坐标
        updateInfo(intersectPoint);
    } else {
        document.getElementById('info').style.display = 'none';
    }
}


// Add points for each city
let weatherData = []; // Global variable

function addPoints() {
    const pointGeometry = new THREE.BufferGeometry();
    const positions = [];
    const colors = [];

    weatherData.forEach((cityData) => {
        const lat = cityData.coord.lat;
        const lon = cityData.coord.lon;

        const phi = (90 - lat) * (Math.PI / 180);
        const theta = (lon + 180) * (Math.PI / 180);

        const x = -10 * Math.sin(phi) * Math.cos(theta);
        const y = 10 * Math.cos(phi);
        const z = 10 * Math.sin(phi) * Math.sin(theta);

        positions.push(x, y, z);

        const color = cityData.is_raining ? new THREE.Color(0x6495ED) : new THREE.Color(0x32CD32);
        colors.push(color.r, color.g, color.b);
    });

    pointGeometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    pointGeometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

    const pointMaterial = new THREE.PointsMaterial({ size: 0.05, vertexColors: true, transparent: true, opacity: 0.7 });
    const points = new THREE.Points(pointGeometry, pointMaterial);
    points.name = 'points';
    earth.add(points);
}


// 初始化倒计时
let countdownInterval = null;

// Fetch weather data and update points
function updateWeatherData() {
    fetch('/api/weather-data')
        .then((response) => response.json())
        .then((response) => {
            weatherData = response.data;
            earth.remove(earth.getObjectByName('points')); // Remove old points
            addPoints();

            // Update statistics
            const stats = weather_data_statics(weatherData);
            document.getElementById('totalCount').textContent = stats.totalCount;
            document.getElementById('rainingCount').textContent = stats.rainingCount;
            document.getElementById('nonRainingCount').textContent = stats.nonRainingCount;
            document.getElementById('rainPercentage').textContent = stats.rainPercentage.toFixed(2);

            // 显示上次更新的时间
            const lastUpdated = new Date(response.timestamp * 1000);
            document.getElementById('lastUpdated').textContent = `Last updated: ${lastUpdated.toLocaleString()}`;

            // 更新倒计时
            updateCountdown(lastUpdated);

            // 如果有任何活动的倒计时间隔，请清除它
            if (countdownInterval) {
                clearInterval(countdownInterval);
            }

            // 设置定期更新倒计时
            countdownInterval = setInterval(() => updateCountdown(lastUpdated), 1000);
        });
}



function updateCountdown(lastUpdated) {
    const now = new Date();
    const nextUpdate = new Date(lastUpdated);
    nextUpdate.setHours(nextUpdate.getHours() + 2);
    nextUpdate.setMinutes(0);
    nextUpdate.setSeconds(0);

    const timeDifference = (nextUpdate - now) / 1000;

    if (timeDifference < 0) {
        document.getElementById('countdown').textContent = "Next update in: running updating";
    } else {
        const hours = Math.floor(timeDifference / 3600);
        const minutes = Math.floor((timeDifference % 3600) / 60);
        const seconds = Math.floor(timeDifference % 60);

        document.getElementById('countdown').textContent = `Next update in: ${hours}:${minutes < 10 ? '0' : ''}${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    }
}


updateWeatherData();

function weather_data_statics(weatherData) {
    let rainingCount = 0;
    let nonRainingCount = 0;

    weatherData.forEach((cityData) => {
        if (cityData.is_raining) {
            rainingCount++;
        } else {
            nonRainingCount++;
        }
    });

    const totalCount = weatherData.length;
    const rainPercentage = (rainingCount / totalCount) * 100;

    return {
        rainingCount,
        nonRainingCount,
        totalCount,
        rainPercentage,
    };
}

function updateInfo(intersectPoint) {
    const cityData = getClosestCity(intersectPoint);

    if (cityData) {
        const info = `${cityData.city}, ${cityData.region}, ${cityData.country}
                      Lat: ${cityData.coord.lat.toFixed(2)} Lon: ${cityData.coord.lon.toFixed(2)}
                      Raining: ${cityData.is_raining ? 'Yes' : 'No'}`;

        // Display the information
        const infoElement = document.getElementById('info');
        infoElement.innerHTML = info.replace(/\n/g, '<br>');
        infoElement.style.display = 'block';
    } else {
        document.getElementById('info').style.display = 'none';
    }
}

function getClosestCity(intersectPoint) {
    let closestCityData = null;
    let closestDistance = Infinity;
    const minDistanceThreshold = 2.5;

    const observerDistance = camera.position.distanceTo(earth.position);
    const scaleFactor = observerDistance / 20; // 20 是初始距离
    const effectiveRadius = 10 * 1; // 10 是初始半径

    weatherData.forEach((cityData) => {
        const lat = cityData.coord.lat;
        const lon = cityData.coord.lon;

        const phi = (90 - lat) * (Math.PI / 180);
        const theta = (lon + 180) * (Math.PI / 180);

        const x = -effectiveRadius * Math.sin(phi) * Math.cos(theta);
        const y = effectiveRadius * Math.cos(phi);
        const z = effectiveRadius * Math.sin(phi) * Math.sin(theta);

        const cityPoint = new THREE.Vector3(x, y, z);
        const distance = cityPoint.distanceTo(intersectPoint);

        if (distance < closestDistance && distance < minDistanceThreshold) {
            closestDistance = distance;
            closestCityData = cityData;
        }
    });

    return closestCityData;
}



// Animation loop
function animate() {
    requestAnimationFrame(animate);
    // earth.rotation.y += 0.001; // 在这里添加地球旋转

    controls.update();
    renderer.render(scene, camera);
}

animate();