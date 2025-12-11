/**
 * Thai ID Card Scanner - JavaScript Client
 * ใช้สำหรับเรียก Local Agent จากหน้าเว็บบน Railway
 *
 * วิธีใช้:
 * 1. ผู้ใช้ต้องรัน Local Agent บนเครื่องของตัวเอง (python thai_id_local_agent.py)
 * 2. Import ไฟล์นี้ในหน้าเว็บ
 * 3. เรียก ThaiIDScanner.scan() เพื่ออ่านบัตร
 */

const ThaiIDScanner = {
  // URL ของ Local Agent (รันบนเครื่องผู้ใช้)
  localAgentUrl: "http://localhost:5051",

  // URL ของ Railway Server (optional - สำหรับส่งข้อมูลไปเก็บ)
  railwayServerUrl: "", // เช่น 'https://your-app.railway.app'

  /**
   * ตรวจสอบว่า Local Agent รันอยู่หรือไม่
   */
  async checkAgent() {
    try {
      const response = await fetch(`${this.localAgentUrl}/api/health`, {
        method: "GET",
        mode: "cors",
      });
      const data = await response.json();
      return {
        running: true,
        hasReader: data.hasReader,
        readers: data.readers,
      };
    } catch (error) {
      return {
        running: false,
        error: "Local Agent ไม่ได้รัน - กรุณารัน python thai_id_local_agent.py",
      };
    }
  },

  /**
   * ดูรายการเครื่องอ่านบัตรที่เชื่อมต่อ
   */
  async getReaders() {
    try {
      const response = await fetch(`${this.localAgentUrl}/api/readers`, {
        method: "GET",
        mode: "cors",
      });
      return await response.json();
    } catch (error) {
      throw new Error("ไม่สามารถเชื่อมต่อ Local Agent ได้");
    }
  },

  /**
   * สแกนบัตรประชาชน
   * @param {boolean} includePhoto - รวมรูปถ่ายด้วยหรือไม่
   * @returns {Object} ข้อมูลจากบัตรประชาชน
   */
  async scan(includePhoto = false) {
    try {
      // ตรวจสอบ Agent ก่อน
      const agentStatus = await this.checkAgent();
      if (!agentStatus.running) {
        throw new Error(agentStatus.error);
      }

      if (!agentStatus.hasReader) {
        throw new Error("ไม่พบเครื่องอ่านบัตร - กรุณาเสียบเครื่อง GLINK");
      }

      // เรียก API สแกน
      const url = includePhoto
        ? `${this.localAgentUrl}/api/scan/photo`
        : `${this.localAgentUrl}/api/scan`;

      const response = await fetch(url, {
        method: "POST",
        mode: "cors",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ includePhoto }),
      });

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.message || "สแกนบัตรไม่สำเร็จ");
      }

      return result;
    } catch (error) {
      if (
        error.message.includes("Failed to fetch") ||
        error.message.includes("NetworkError")
      ) {
        throw new Error(
          "ไม่สามารถเชื่อมต่อ Local Agent ได้ - กรุณาตรวจสอบว่า:\n1. รัน python thai_id_local_agent.py แล้ว\n2. เสียบเครื่องอ่านบัตรแล้ว\n3. ใส่บัตรประชาชนในเครื่องอ่านแล้ว"
        );
      }
      throw error;
    }
  },

  /**
   * สแกนบัตรและส่งข้อมูลไป Railway Server
   * @param {string} railwayUrl - URL ของ Railway server
   * @param {boolean} includePhoto - รวมรูปถ่ายด้วยหรือไม่
   */
  async scanAndSendToServer(railwayUrl, includePhoto = false) {
    // สแกนบัตร
    const scanResult = await this.scan(includePhoto);

    if (scanResult.success && railwayUrl) {
      // ส่งข้อมูลไป Railway
      try {
        await fetch(`${railwayUrl}/api/thaiid/receive`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(scanResult.data),
        });
      } catch (error) {
        console.warn("ไม่สามารถส่งข้อมูลไป Railway ได้:", error);
      }
    }

    return scanResult;
  },
};

// ==================== ตัวอย่างการใช้งาน ====================

/*
// 1. ตรวจสอบ Agent
const status = await ThaiIDScanner.checkAgent();
console.log(status);
// { running: true, hasReader: true, readers: ['Generic EMV Smartcard Reader 0'] }

// 2. สแกนบัตร (ไม่รวมรูป)
try {
    const result = await ThaiIDScanner.scan();
    console.log('เลขบัตร:', result.data.cid);
    console.log('ชื่อ:', result.data.name.th.fullName);
    console.log('ที่อยู่:', result.data.address.full);
} catch (error) {
    alert(error.message);
}

// 3. สแกนบัตรพร้อมรูป
const resultWithPhoto = await ThaiIDScanner.scan(true);
if (resultWithPhoto.data.photo) {
    document.getElementById('photo').src = 'data:image/jpeg;base64,' + resultWithPhoto.data.photo;
}

// 4. สแกนแล้วส่งไป Railway
const result = await ThaiIDScanner.scanAndSendToServer('https://your-app.railway.app');
*/

// Export for module usage
if (typeof module !== "undefined" && module.exports) {
  module.exports = ThaiIDScanner;
}
