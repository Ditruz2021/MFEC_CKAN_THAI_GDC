document.addEventListener('DOMContentLoaded', function () {
    // โหลดการตั้งค่าขนาดฟอนต์จาก localStorage
    const savedFontSize = localStorage.getItem('fontSize');
    if (savedFontSize) {
      adjustFontSize(savedFontSize);
      document.querySelectorAll('.font-size-btn').forEach(button => {
        if (button.getAttribute('data-size') === savedFontSize) {
          button.classList.add('active');
        }
      });
    }
  });

  document.querySelectorAll('.font-size-btn').forEach(button => {
    button.addEventListener('click', function () {
      // ลบคลาส active จากปุ่มทั้งหมด
      document.querySelectorAll('.font-size-btn').forEach(btn => btn.classList.remove('active'));
      // เพิ่มคลาส active ให้กับปุ่มที่ถูกคลิก
      this.classList.add('active');

      // ปรับขนาดฟอนต์และบันทึกการตั้งค่า
      const size = this.getAttribute('data-size');
      adjustFontSize(size);
      localStorage.setItem('fontSize', size);
    });
  });

  function adjustFontSize(size) {
    const elements = document.querySelectorAll('body, h1, h2, h3, h4, h5, h6, p, a');
    elements.forEach(element => {
      if (size === 'smaller') {
        const currentFontSize = parseInt(window.getComputedStyle(element).fontSize);
        element.style.fontSize = (currentFontSize - 2) + 'px';
      } else if (size === 'larger') {
        const currentFontSize = parseInt(window.getComputedStyle(element).fontSize);
        element.style.fontSize = (currentFontSize + 4) + 'px';
      } else {
        // คืนค่าเริ่มต้นของฟอนต์
        element.style.fontSize = '';
      }
    });
  }