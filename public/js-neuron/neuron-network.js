// SLH Neuron Network Visualization
class NeuronNetwork {
    constructor() {
        this.canvas = document.getElementById('neuron-canvas');
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.width = window.innerWidth;
        this.height = window.innerHeight;
        
        // Neuron positions (central + orbiting)
        this.center = { x: this.width / 2, y: this.height / 2 };
        this.neurons = [];
        this.connections = [];
        
        this.init();
        this.animate();
        this.handleResize();
    }
    
    init() {
        // Create central neuron (SLH Core)
        this.coreNeuron = {
            x: this.width / 2,
            y: this.height / 2,
            radius: 60,
            pulse: 0,
            pulseDirection: 1
        };
        
        // Create orbiting neurons (modules)
        const modules = [
            { label: 'Wallet', angle: 0, distance: 180, color: '#00CEC9' },
            { label: 'Staking', angle: 45, distance: 200, color: '#FFD32A' },
            { label: 'Trade', angle: 90, distance: 220, color: '#6C5CE7' },
            { label: 'Bots', angle: 135, distance: 190, color: '#00B894' },
            { label: 'Earn', angle: 180, distance: 210, color: '#FF4757' },
            { label: 'Referral', angle: 225, distance: 195, color: '#A29BFE' },
            { label: 'Community', angle: 270, distance: 185, color: '#00CEC9' },
            { label: 'Academy', angle: 315, distance: 205, color: '#FFD32A' }
        ];
        
        modules.forEach((mod, i) => {
            this.neurons.push({
                ...mod,
                x: this.center.x + Math.cos(mod.angle * Math.PI / 180) * mod.distance,
                y: this.center.y + Math.sin(mod.angle * Math.PI / 180) * mod.distance,
                radius: 25,
                angle: mod.angle,
                distance: mod.distance,
                speed: 0.002 * (i + 1),
                pulse: 0
            });
        });
        
        // Create connections
        this.neurons.forEach(neuron => {
            this.connections.push({
                from: this.coreNeuron,
                to: neuron
            });
        });
    }
    
    drawNeuron(x, y, radius, color, pulse = 0) {
        const ctx = this.ctx;
        const glowRadius = radius + pulse * 5;
        
        ctx.beginPath();
        ctx.arc(x, y, glowRadius, 0, Math.PI * 2);
        ctx.fillStyle = gba(, , , 0.2);
        ctx.fill();
        
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        const grad = ctx.createLinearGradient(x - radius, y - radius, x + radius, y + radius);
        grad.addColorStop(0, color);
        grad.addColorStop(1, color + 'cc');
        ctx.fillStyle = grad;
        ctx.fill();
        
        ctx.shadowBlur = 15;
        ctx.shadowColor = color;
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.shadowBlur = 0;
    }
    
    drawConnection(from, to) {
        const ctx = this.ctx;
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        
        const grad = ctx.createLinearGradient(from.x, from.y, to.x, to.y);
        grad.addColorStop(0, '#6C5CE7');
        grad.addColorStop(1, '#00CEC9');
        
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1.5;
        ctx.stroke();
    }
    
    animate() {
        if (!this.ctx) return;
        
        this.ctx.clearRect(0, 0, this.width, this.height);
        
        // Update core neuron pulse
        this.coreNeuron.pulse += 0.02 * this.coreNeuron.pulseDirection;
        if (this.coreNeuron.pulse > 1 || this.coreNeuron.pulse < 0) {
            this.coreNeuron.pulseDirection *= -1;
        }
        
        // Update orbiting neurons
        this.neurons.forEach(neuron => {
            neuron.angle += neuron.speed;
            neuron.x = this.center.x + Math.cos(neuron.angle) * neuron.distance;
            neuron.y = this.center.y + Math.sin(neuron.angle) * neuron.distance;
            neuron.pulse = Math.sin(Date.now() * 0.003 * (neuron.angle + 1)) * 0.3;
        });
        
        // Draw connections
        this.connections.forEach(conn => {
            this.drawConnection(conn.from, conn.to);
        });
        
        // Draw orbiting neurons
        this.neurons.forEach(neuron => {
            this.drawNeuron(neuron.x, neuron.y, neuron.radius, neuron.color, neuron.pulse);
        });
        
        // Draw core neuron
        this.drawNeuron(this.coreNeuron.x, this.coreNeuron.y, 
                       this.coreNeuron.radius + this.coreNeuron.pulse * 10, 
                       '#6C5CE7', this.coreNeuron.pulse);
        
        requestAnimationFrame(() => this.animate());
    }
    
    handleResize() {
        window.addEventListener('resize', () => {
            this.width = window.innerWidth;
            this.height = window.innerHeight;
            this.center = { x: this.width / 2, y: this.height / 2 };
            this.canvas.width = this.width;
            this.canvas.height = this.height;
            this.init();
        });
        this.canvas.width = this.width;
        this.canvas.height = this.height;
    }
}

// Initialize when DOM ready
document.addEventListener('DOMContentLoaded', () => {
    new NeuronNetwork();
});
