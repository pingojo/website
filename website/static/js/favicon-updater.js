      let count = 0;
      let originalFavicon;
      
      function updateFavicon(count) {
        const favicon = document.querySelector('link[rel=icon]');
        const faviconSize = 16;
        const canvas = document.createElement('canvas');
        canvas.width = faviconSize;
        canvas.height = faviconSize;
        const context = canvas.getContext('2d');
        const img = new Image();
        img.crossOrigin = 'anonymous';
      
        if (!originalFavicon) {
          originalFavicon = favicon.href;
        }
      
        if (favicon === null) return;
        img.src = originalFavicon;
      
        img.onload = () => {
          if (context === null) return;
          context.drawImage(img, 0, 0, faviconSize, faviconSize);
          if (count > 0) {
            // Draw Notification Rounded Rectangle
            context.fillStyle = 'rgba(255, 255, 255, 0.9)';
            context.beginPath();
            context.roundRect(2, 6, 12, 12, 2).fill();
      
            // Draw Notification Number
            context.font = '11px ';
            context.textAlign = 'center';
            context.textBaseline = 'middle';
            context.fillStyle = '#000000';
            context.fillText(String(count), faviconSize / 2, faviconSize - 5);
      
            // Replace favicon
            favicon.href = canvas.toDataURL('image/png');
          }
        };
      }
      
      // Add roundRect function to the canvas
      CanvasRenderingContext2D.prototype.roundRect = function (x, y, width, height, radius) {
        if (typeof radius === 'undefined') {
          radius = 5;
        }
        this.beginPath();
        this.moveTo(x + radius, y);
        this.lineTo(x + width - radius, y);
        this.quadraticCurveTo(x + width, y, x + width, y + radius);
        this.lineTo(x + width, y + height - radius);
        this.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        this.lineTo(x + radius, y + height);
        this.quadraticCurveTo(x, y + height, x, y + height - radius);
        this.lineTo(x, y + radius);
        this.quadraticCurveTo(x, y, x + radius, y);
        this.closePath();
        return this;
      };
      
      // Increment count and update favicon every second
// fetch('/api/application_count')
//   .then(response => response.json())
//   .then(data => {
//     if(data.count > 0) {
//       console.log(data);
//       updateFavicon(data.count);
//     } else {
//       updateFavicon(0);
//     }
//   })
//   .catch(error => {
//     console.error('Error fetching application count:', error);
//   });

// setInterval(() => {
//   fetch('/api/application_count')
//     .then(response => response.json())
//     .then(data => {
//       console.log(data);
//       if(data.count > 0) {
//         updateFavicon(data.count);
//       } else {
//         updateFavicon(0);
//       }
//     })
//     .catch(error => {
//       console.error('Error fetching application count:', error);
//     });
// }, 50000);