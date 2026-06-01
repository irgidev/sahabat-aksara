"""
V8 SCORING ENGINE - Feature-Based Character Recognition (Robust v2)
====================================================================
NO free points. NO template matching. NO skeleton pipelines.
Each character has explicit feature rules. Score starts at 0.

Scoring Bands:
  GOLD:   All required features pass  -> 65-100% (2-3 stars)
  SILVER: Some features pass          -> 25-55%  (1 star)
  BRONZE: Few/no features             -> 0-20%    (0 stars)

CRITICAL FAIL: If essential feature fails -> max 22%

FIX v9: Relaxed thresholds for kid handwriting (PAUD age 4-6)
"""

import cv2
import numpy as np






class F:
    @staticmethod
    def px(img): return int(np.sum(img > 127))


    @staticmethod
    def has_enclosed(img):
        """Has at least one enclosed region (hole inside shape)."""
        inv = cv2.bitwise_not((img > 127).astype(np.uint8) * 255)
        n, labels, stats, _ = cv2.connectedComponentsWithStats(inv)
        if n < 3: return False
        h, w = img.shape
        for i in range(1, n):
            area = stats[i, cv2.CC_STAT_AREA]
            x, y, cw, ch = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]

            if area > h * w * 0.02 and cw < w - 1 and ch < h - 1:
                return True
        return False

    @staticmethod
    def n_enclosed(img):
        inv = cv2.bitwise_not((img > 127).astype(np.uint8) * 255)
        n, labels, stats, _ = cv2.connectedComponentsWithStats(inv)
        count = 0; h, w = img.shape
        for i in range(1, n):
            if stats[i, cv2.CC_STAT_AREA] > h * w * 0.02 and stats[i, cv2.CC_STAT_WIDTH] < w - 1 and stats[i, cv2.CC_STAT_HEIGHT] < h - 1:
                count += 1
        return count


    @staticmethod
    def vert_stems(img, n=1):
        cs = np.sum((img > 127).astype(np.uint8) * 255 > 0, axis=0)
        return int(np.sum(cs >= img.shape[0] * 0.22))

    @staticmethod
    def has_vert_line(img):
        """Has at least one dominant vertical line."""
        cs = np.sum((img > 127).astype(np.uint8) * 255 > 0, axis=0)
        return np.any(cs >= img.shape[0] * 0.20)

    @staticmethod
    def single_vert(img):
        """One dominant vertical stroke (like I)."""
        cs = np.sum((img > 127).astype(np.uint8) * 255 > 0, axis=0)
        strong = np.sum(cs >= img.shape[0] * 0.20)

        return strong >= 1, 0.7

    @staticmethod
    def dual_vert(img):
        """Two vertical strokes (like H, U, M, N)."""
        cs = np.sum((img > 127).astype(np.uint8) * 255 > 0, axis=0)
        strong_cols = np.where(cs >= img.shape[0] * 0.22)[0]
        if len(strong_cols) < 4: return False

        mid = img.shape[1] // 2
        left_any = np.any(strong_cols < mid - 3)
        right_any = np.any(strong_cols > mid + 3)
        return left_any and right_any


    @staticmethod
    def hline(img, region='any'):
        rs = np.sum((img > 127).astype(np.uint8) * 255 > 0, axis=1)
        h, w = img.shape
        t = w * 0.15
        if region == 'top': rs = rs[:int(h * .30)]
        elif region == 'bottom': rs = rs[int(h * .70):]
        elif region == 'mid': rs = rs[int(h * .35):int(h * .65)]
        return bool(np.any(rs >= t))


    @staticmethod
    def diag_count(img, min_len=6):
        edges = cv2.Canny((img > 127).astype(np.uint8) * 255, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 5, min_len, 3)
        if lines is None: return 0
        c = 0
        for l in lines:
            dx, dy = abs(l[0][2] - l[0][0]), abs(l[0][3] - l[0][1])
            if dx > 3 and dy > 3:
                a = abs(np.degrees(np.arctan2(dy, dx)))
                if 15 <= a <= 75 or 105 <= a <= 165: c += 1
        return c

    @staticmethod
    def diag_any(img):
        return F.diag_count(img) >= 1

    @staticmethod
    def diag_dr(img):
        """Diagonal going down-right."""
        edges = cv2.Canny((img > 127).astype(np.uint8) * 255, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 5, 8, 3)
        if lines is None: return False
        for l in lines:
            dx = l[0][2] - l[0][0]
            dy = l[0][3] - l[0][1]
            if dx > 4 and dy > 4:
                return True
        return False


    @staticmethod
    def is_round(img):
        cnts, _ = cv2.findContours((img > 127).astype(np.uint8) * 255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts: return False
        c = max(cnts, key=cv2.contourArea); a = float(cv2.contourArea(c)); p = cv2.arcLength(c, True)
        circ = 4 * np.pi * a / (p ** 2) if p > 0 else 0
        pts = np.argwhere(img > 127)
        if len(pts) < 10: return False
        ys, xs = zip(*pts); ar = float(max(xs) - min(xs)) / max(max(ys) - min(ys), 1)

        return circ > 0.28 and 0.35 < ar < 2.5

    @staticmethod
    def roundish(img):
        """Somewhat round - not fully circular but not angular/linear either."""
        cnts, _ = cv2.findContours((img > 127).astype(np.uint8) * 255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts: return False
        c = max(cnts, key=cv2.contourArea); a = float(cv2.contourArea(c)); p = cv2.arcLength(c, True)
        circ = 4 * np.pi * a / (p ** 2) if p > 0 else 0
        pts = np.argwhere(img > 127)
        if len(pts) < 10: return False
        ys, xs = zip(*pts); ar = float(max(xs) - min(xs)) / max(max(ys) - min(ys), 1)

        if circ < 0.18 or ar < 0.20 or ar > 5.0: return False

        g = (img > 127).astype(np.uint8) * 255
        corners = cv2.cornerHarris(g, 3, 3, 0.04)
        n_sharp = int(np.sum(corners > 0.01 * corners.max()))

        corner_ratio = n_sharp / max(len(pts), 1) * 100

        return corner_ratio < 8.0 or circ > 0.25


    @staticmethod
    def sym_v(img, strict=True):
        b = (img > 127).astype(np.uint8); h, w = b.shape
        L = b[:, :w // 2]; R = b[:, w - w // 2:]
        m = min(L.shape[1], R.shape[1]); L, R = L[:, :m], R[:, :m]
        return np.sum(L == np.fliplr(R)) / L.size > (.55 if strict else .40)

    @staticmethod
    def sym_h(img):
        b = (img > 127).astype(np.uint8); h = b.shape[0]
        T = b[:h // 2, :]; B = b[h - h // 2:, :]; m = min(T.shape[0], B.shape[0])
        return np.sum(T == np.flipud(B[:, :m])) / T.size > .45


    @staticmethod
    def center_off(img):
        M = cv2.moments((img > 127).astype(np.uint8) * 255)
        if M['m00'] < 10: return 99.0
        cx, cy = M['m10'] / M['m00'], M['m01'] / M['m00']; h, w = img.shape
        return (np.sqrt((cx - w / 2) ** 2 + (cy - h / 2) ** 2) / (np.sqrt((w / 2) ** 2 + (h / 2) ** 2))) * 100

    @staticmethod
    def top_heavy(img):
        b = (img > 127).astype(np.uint8); h = b.shape[0]
        return np.sum(b[:h // 2] > 0) > np.sum(b[h // 2:] > 0) * 1.25

    @staticmethod
    def bottom_heavy(img):
        b = (img > 127).astype(np.uint8); h = b.shape[0]
        return np.sum(b[h // 2:] > 0) > np.sum(b[:h // 2] > 0) * 1.25

    @staticmethod
    def aspect(img):
        pts = np.argwhere(img > 127)
        if len(pts) < 5: return 1.0
        ys, xs = zip(*pts)
        return float(max(xs) - min(xs)) / max(max(ys) - min(ys), 1)


    @staticmethod
    def complexity(img):
        cnts, _ = cv2.findContours((img > 127).astype(np.uint8) * 255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts: return 0.0
        ta = sum(cv2.contourArea(c) for c in cnts); tp = sum(cv2.arcLength(c, True) for c in cnts)
        return tp / max(ta, 1)


    @staticmethod
    def z_shape(img): return F.hline(img, 'top') and F.hline(img, 'bottom') and F.diag_any(img)
    @staticmethod
    def s_curve(img):
        b = (img > 127).astype(np.uint8) * 255; h = b.shape[0]
        Mt, Mb = cv2.moments(b[:h // 2, :]), cv2.moments(b[h // 2:, :])
        if Mt['m00'] < 10 or Mb['m00'] < 10: return False
        tcx, bcx = Mt['m10'] / Mt['m00'], Mb['m10'] / Mb['m00']; mid = b.shape[1] / 2
        return (tcx > mid and bcx < mid) or (tcx < mid and bcx > mid)






RULES = {

    'A': {'required': ['apex_top', 'wider_at_bottom', 'crossbar_mid'],
          'bonus': ['sym_v'], 'anti': ['is_round'], 'min_px': 250},
    'B': {'required': ['has_enclosed', 'vert_stem', 'dual_blob'],
          'bonus': [], 'anti': [], 'min_px': 320},
    'C': {'required': ['roundish', 'no_straight_dom'],
          'bonus': ['c_open_shape'], 'anti': [], 'min_px': 250},
    'D': {'required': ['vert_stem', 'not_narrow'],
          'bonus': [], 'anti': [], 'min_px': 280},
    'E': {'required': ['vert_stem', 'hline_top', 'hline_mid'],
          'bonus': ['hline_bottom'], 'anti': ['has_enclosed', 'is_round'], 'min_px': 280},
    'F': {'required': ['vert_stem', 'hline_top', 'hline_top_or_mid'],
          'bonus': [], 'anti': ['has_enclosed', 'hline_bottom', 'is_round'], 'min_px': 250},
    'G': {'required': ['has_crossbar', 'not_straight'],
          'bonus': [], 'anti': [], 'min_px': 280},
    'H': {'required': ['dual_vert', 'hline_mid'],
          'bonus': ['sym_v'], 'anti': ['has_enclosed', 'is_round'], 'min_px': 320},
    'I': {'required': ['vert_dominant', 'centered'],
          'bonus': [], 'anti': ['has_enclosed', 'diag_any', 'wide_shape'], 'min_px': 180},
    'J': {'required': ['hook_or_curve_bot', 'no_dual_vert'],
          'bonus': [], 'anti': ['dual_vert'], 'min_px': 220},
    'K': {'required': ['vert_stem', 'diag_ge2'],
          'bonus': [], 'anti': ['has_enclosed', 'is_round'], 'min_px': 320},
    'L': {'required': ['vert_stem', 'hline_bottom', 'no_hline_top'],
          'bonus': [], 'anti': ['has_enclosed', 'is_round', 'hline_top'], 'min_px': 220},
    'M': {'required': ['dual_vert', 'v_at_top'],
          'bonus': ['sym_loose'], 'anti': ['has_enclosed', 'is_round'], 'min_px': 380},
    'N': {'required': ['dual_vert', 'diag_any'],
          'bonus': [], 'anti': ['has_enclosed', 'is_round'], 'min_px': 350},
    'O': {'required': ['has_enclosed', 'roundish', 'compact'],
          'bonus': ['sym_loose'], 'anti': ['straight_long'], 'min_px': 320},
    'P': {'required': ['has_enclosed', 'vert_stem', 'top_half_heavy'],
          'bonus': [], 'anti': ['bottom_heavy', 'very_round'], 'min_px': 320},
    'Q': {'required': ['has_enclosed', 'roundish'],
          'bonus': [], 'anti': [], 'min_px': 350},
    'R': {'required': ['has_enclosed', 'vert_stem', 'diag_any'],
          'bonus': [], 'anti': ['very_round'], 'min_px': 350},
    'S': {'required': ['s_curve', 'not_straight'],
          'bonus': [], 'anti': ['has_enclosed', 'z_shape'], 'min_px': 280},
    'T': {'required': ['hline_top', 'vert_center', 'sym_loose'],
          'bonus': [], 'anti': ['has_enclosed', 'hline_bottom', 'is_round'], 'min_px': 250},
    'U': {'required': ['dual_vert', 'curve_at_bottom', 'open_at_top'],
          'bonus': [], 'anti': ['has_enclosed'], 'min_px': 280},
    'V': {'required': ['v_diagonals', 'pointed_bottom'],
          'bonus': ['sym_loose'], 'anti': ['has_enclosed', 'is_round'], 'min_px': 250},
    'W': {'required': ['wider_than_tall', 'has_ink_everywhere'],
          'bonus': ['sym_loose'], 'anti': ['has_enclosed', 'is_round'], 'min_px': 380},
    'X': {'required': ['diag_cross', 'centered'],
          'bonus': ['sym_loose'], 'anti': ['has_enclosed', 'is_round'], 'min_px': 280},
    'Y': {'required': ['v_upper_half', 'vert_lower_half'],
          'bonus': ['sym_loose'], 'anti': ['has_enclosed', 'is_round'], 'min_px': 280},
    'Z': {'required': ['z_shape', 'hline_top', 'hline_bottom'],
          'bonus': [], 'anti': ['has_enclosed', 'is_round'], 'min_px': 280},


    'a': {'required': ['has_enclosed', 'roundish'],
          'bonus': [], 'anti': ['tall_shape'], 'min_px': 250},
    'b': {'required': ['vert_left_side', 'has_enclosed', 'roundish_any'],
          'bonus': [], 'anti': [], 'min_px': 320},
    'c': {'required': ['compact', 'no_straight_dom'],
          'bonus': [], 'anti': ['has_enclosed', 'tall_shape'], 'min_px': 180},
    'd': {'required': ['vert_right_side', 'has_enclosed', 'roundish_any'],
          'bonus': [], 'anti': [], 'min_px': 320},
    'e': {'required': ['hline_mid'],
          'bonus': ['roundish', 'has_enclosed'], 'anti': ['tall_shape'], 'min_px': 250},
    'l': {'required': ['vert_dominant', 'centered'],
          'bonus': [], 'anti': ['has_enclosed', 'wide_shape'], 'min_px': 180},
    'm': {'required': ['dual_vert'],
          'bonus': ['roundish_any', 'v_at_top'], 'anti': ['has_enclosed', 'tall_shape'], 'min_px': 280},
    'n': {'required': ['vert_left_side'],
          'bonus': ['roundish_any', 'diag_any'], 'anti': ['has_enclosed', 'tall_shape'], 'min_px': 250},
    'o': {'required': ['has_enclosed', 'roundish'],
          'bonus': ['sym_loose'], 'anti': ['straight_long'], 'min_px': 250},
    'p': {'required': ['has_enclosed', 'vert_stem'],
          'bonus': ['roundish'], 'anti': ['top_half_heavy'], 'min_px': 280},
    'r': {'required': ['vert_left_side'],
          'bonus': ['diag_any'], 'anti': ['has_enclosed', 'tall_shape'], 'min_px': 220},
    't': {'required': ['vert_center', 'hline_top'],
          'bonus': [], 'anti': ['has_enclosed'], 'min_px': 220},
    'u': {'required': ['dual_vert', 'curve_at_bottom'],
          'bonus': [], 'anti': ['has_enclosed', 'hline_top'], 'min_px': 250},
    'v': {'required': ['v_diagonals'],
          'bonus': ['sym_loose'], 'anti': ['has_enclosed', 'is_round'], 'min_px': 220},
    'w': {'required': ['wider_than_tall', 'v_diagonals'],
          'bonus': ['sym_loose'], 'anti': ['has_enclosed', 'is_round'], 'min_px': 320},
    'x': {'required': ['diag_cross', 'centered'],
          'bonus': ['sym_loose'], 'anti': ['has_enclosed', 'is_round'], 'min_px': 250},
    'y': {'required': ['v_upper_half', 'diag_dr'],
          'bonus': [], 'anti': ['has_enclosed'], 'min_px': 250},
    'z': {'required': ['z_shape'],
          'bonus': ['hline_top', 'hline_bottom'], 'anti': ['has_enclosed', 'is_round'], 'min_px': 220},


    '0': {'required': ['has_enclosed', 'roundish', 'centered'],
          'bonus': ['sym_loose'], 'anti': ['straight_long'], 'min_px': 350},
    '1': {'required': ['vert_dominant', 'narrow_shape'],
          'bonus': [], 'anti': ['has_enclosed', 'wide_shape', 'is_round'], 'min_px': 40},
    '2': {'required': ['curve_top_half', 'diag_sweep', 'hline_bottom'],
          'bonus': [], 'anti': ['has_enclosed'], 'min_px': 280},
    '3': {'required': ['curve_upper', 'two_curves'],
          'bonus': [], 'anti': ['has_enclosed', 'long_straight'], 'min_px': 250},
    '4': {'required': ['vert_stem', 'hline_mid', 'hline_top'],
          'bonus': [], 'anti': ['has_enclosed', 'is_round'], 'min_px': 280},
    '5': {'required': ['hline_top', 'vert_left_side', 'curve_lower_half'],
          'bonus': [], 'anti': ['has_enclosed', 'diag_any'], 'min_px': 280},
    '6': {'required': ['curve_lower', 'has_ink_top'],
          'bonus': [], 'anti': ['straight_long'], 'min_px': 320},
    '7': {'required': ['hline_top', 'diag_any'],
          'bonus': [], 'anti': ['has_enclosed', 'is_round'], 'min_px': 220},
    '8': {'required': ['has_enclosed', 'sym_loose'],
          'bonus': ['enclosed_ge2', 'roundish'], 'anti': [], 'min_px': 380},
    '9': {'required': ['has_enclosed', 'roundish'],
          'bonus': [], 'anti': ['straight_long'], 'min_px': 320},
}






def check(feat, img):
    """Evaluate one feature. Returns (bool, confidence)."""
    try:
        h, w = img.shape
        b = (img > 127).astype(np.uint8) * 255


        if feat == 'has_enclosed':
            r = F.has_enclosed(img); return r, (0.85 if r else 0.0)
        if feat == 'enclosed_ge2':
            r = F.n_enclosed(img) >= 2; return r, min(F.n_enclosed(img) / 2, 1.0)
        if feat == 'big_enclosed':
            inv = cv2.bitwise_not(b)
            nl, _, stats, _ = cv2.connectedComponentsWithStats(inv)
            if nl < 3: return False, 0.0
            for i in range(1, nl):
                if stats[i, cv2.CC_STAT_AREA] > 18: return True, 0.75
            return False, 0.0


        if feat == 'vert_stem' or feat == 'vert_stem_1':
            return F.has_vert_line(img), 0.75
        if feat == 'vert_left_side' or feat == 'vert_left':
            cs = np.sum(b > 0, axis=0)
            return np.any(cs[:w // 2] >= h * 0.22), 0.7
        if feat == 'vert_right_side' or feat == 'vert_right':
            cs = np.sum(b > 0, axis=0)
            return np.any(cs[w // 2:] >= h * 0.22), 0.7
        if feat == 'vert_dominant' or feat == 'single_vert':
            return F.single_vert(img)
        if feat == 'dual_vert':
            return F.dual_vert(img), 0.75
        if feat == 'vert_lower_half':
            bot = b[h // 2:]
            cs = np.sum(bot > 0, axis=0)
            return np.any(cs >= bot.shape[0] * 0.25), 0.65
        if feat == 'vert_center':
            cs = np.sum(b > 0, axis=0)
            mid = w // 2
            return np.any(cs[max(0, mid - 5):mid + 6] >= h * 0.25), 0.7


        if feat == 'hline_top': return F.hline(img, 'top'), 0.8
        if feat == 'hline_bottom': return F.hline(img, 'bottom'), 0.8
        if feat == 'hline_mid': return F.hline(img, 'mid'), 0.8
        if feat == 'hline_any': return F.hline(img, 'any'), 0.6
        if feat == 'no_hline_top': return not F.hline(img, 'top'), 0.6
        if feat == 'hline_top_or_mid': return F.hline(img, 'mid') or F.hline(img, 'top'), 0.7


        if feat == 'diag_any': return F.diag_any(img), 0.7
        if feat == 'diag_dr': return F.diag_dr(img), 0.7
        if feat == 'diag_ge2' or feat == 'diag_cross':
            return F.diag_count(img) >= 2, 0.75
        if feat == 'diag_sweep':

            return F.diag_dr(img) or F.diag_count(img, 5) >= 1, 0.6


        if feat == 'is_round' or feat == 'very_round':
            return F.is_round(img), 0.75
        if feat == 'roundish':
            return F.roundish(img), 0.7
        if feat == 'roundish_small':
            return F.roundish(img), 0.6
        if feat == 'curve_at_bottom' or feat == 'curve_bot' or feat == 'curve_lower' or feat == 'curve_lower_half':

            bot_region = b[int(h * 0.55):]
            edges_bot = cv2.Canny(bot_region, 50, 150)
            ink_bot = np.sum(bot_region > 0)
            edge_density = np.sum(edges_bot > 0) / max(edges_bot.size, 1)

            row_ink = np.sum(bot_region > 0, axis=1)
            non_empty_rows = np.sum(row_ink > 3)

            if non_empty_rows < 3: return False, 0.3
            widths = []
            for i in range(bot_region.shape[0]):
                cols = np.where(bot_region[i] > 0)[0]
                if len(cols) > 1: widths.append(cols[-1] - cols[0])
            if len(widths) < 3: return False, 0.3
            width_var = np.std(widths) / max(np.mean(widths), 1)
            return width_var > 0.08 or edge_density > 0.05, 0.6
        if feat == 'curve_top_half' or feat == 'curve_upper' or feat == 'curve_top':
            top_region = b[:int(h * 0.45)]
            edges_top = cv2.Canny(top_region, 50, 150)
            row_ink = np.sum(top_region > 0, axis=1)
            non_empty_rows = np.sum(row_ink > 3)
            if non_empty_rows < 3: return False, 0.3
            widths = []
            for i in range(top_region.shape[0]):
                cols = np.where(top_region[i] > 0)[0]
                if len(cols) > 1: widths.append(cols[-1] - cols[0])
            if len(widths) < 3: return False, 0.3
            width_var = np.std(widths) / max(np.mean(widths), 1)
            return width_var > 0.08, 0.6


        if feat == 'c_open_shape' or feat == 'c_loose' or feat == 'c_open':

            if F.has_enclosed(img): return False, 0.0
            circ_ok = F.roundish(img) or _circ_fallback(img)

            left_ink = np.sum(b[:, :w * 2 // 3] > 0)
            right_ink = np.sum(b[:, w // 3:] > 0)
            open_right = left_ink > right_ink * 1.3
            return (circ_ok or open_right) and open_right, 0.65
        if feat == 'no_straight_dom' or feat == 'not_straight' or feat == 'no_straight_long':

            edges = cv2.Canny(b, 50, 150)
            ink = np.sum(b > 0)
            edge_px = np.sum(edges > 0)

            if edge_px < ink * 0.15: return False, 0.3
            ln = cv2.HoughLinesP(edges, 1, np.pi / 180, 6, 10, 3)
            if ln is None:


                pts = np.argwhere(img > 127)
                if len(pts) < 30: return False, 0.2

                density = ink / max(len(pts), 1)
                return density < 1.8, 0.55
            total_ln = sum(np.sqrt((l[0][2] - l[0][0])**2 + (l[0][3] - l[0][1])**2) for l in ln)
            return total_ln < ink * 0.28, 0.65
        if feat == 'long_straight' or feat == 'straight_long' or feat == 'straight_dom':
            edges = cv2.Canny(b, 50, 150)
            ln = cv2.HoughLinesP(edges, 1, np.pi / 180, 6, 14, 3)
            if ln is None: return False, 0.0
            total_ln = sum(np.sqrt((l[0][2] - l[0][0]) ** 2 + (l[0][3] - l[0][1]) ** 2) for l in ln)
            return total_ln > np.sum(b > 0) * 0.35, 0.6


        if feat == 'v_shape' or feat == 'v_diagonals':
            dc = F.diag_count(img, 4)
            if dc >= 2: return True, 0.75
            if dc >= 1:
                bot = (img>127).astype(np.uint8)*255; h=img.shape[0]
                bbot=bot[int(h*0.70):]; cs=np.sum(bbot>0,axis=0)
                act=np.where(cs>0)[0]
                if len(act)>=2 and (act[-1]-act[0])<bbot.shape[1]*0.50:
                    return True, 0.65
            return False, 0.5
        if feat == 'v_at_top' or feat == 'v_upper' or feat == 'v_upper_half':

            top = b[:int(h * 0.50)]
            dc_top = F.diag_count_img(top, 4)

            bot = b[int(h * 0.50):]
            dc_bot = F.diag_count_img(bot, 4)
            return dc_top >= 1 and dc_top >= dc_bot, 0.65
        if feat == 'z_shape': return F.z_shape(img), 0.8
        if feat == 's_curve': return F.s_curve(img), 0.7


        if feat == 'top_heavy' or feat == 'top_half_heavy':
            return F.top_heavy(img), 0.7
        if feat == 'bottom_heavy': return F.bottom_heavy(img), 0.7
        if feat == 'centered': return F.center_off(img) < 28, 0.7
        if feat == 'narrow_shape' or feat == 'narrow':
            return F.aspect(img) < 0.55, 0.7
        if feat == 'wide_shape' or feat == 'wide' or feat == 'is_wide':
            return F.aspect(img) > 1.3, 0.65
        if feat == 'tall_shape' or feat == 'tall':
            return F.aspect(img) < 0.48, 0.6
        if feat == 'compact':
            pts = np.argwhere(img > 127)
            if len(pts) < 15: return False, 0.3
            ys, xs = zip(*pts); ww = max(xs) - min(xs); hh = max(ys) - min(ys)
            ar = float(ww) / max(hh, 1); fill = len(pts) / max(ww * hh, 1)
            dim_ratio = max(ww, hh) / min(max(ww, hh), min(ww, hh))
            return 0.35 < ar < 3.0 and fill > 0.10 and dim_ratio < 4.0, 0.6


        if feat == 'sym_v': return F.sym_v(img, True), 0.8
        if feat == 'sym_h': return F.sym_h(img), 0.7
        if feat == 'sym_loose':
            return F.sym_v(img, False) or F.sym_h(img), 0.6


        if feat == 'open_at_top' or feat == 'top_heavy_inv':
            top_ink = np.sum(img[:int(h * 0.28)] > 127)
            bot_ink = np.sum(img[int(h * 0.55):] > 127)
            return top_ink < max(bot_ink * 0.8, 15), 0.6
        if feat == 'pointy_bot' or feat == 'pointed_bottom':

            bot = b[int(h * 0.70):]
            cs = np.sum(bot > 0, axis=0)
            active = np.where(cs > 0)[0]
            if len(active) < 2: return True, 0.5
            span = active[-1] - active[0]
            return span < bot.shape[1] * 0.45, 0.6
        if feat == 'wide_bottom':
            tw = _width_in(b, 0, h // 2)
            bw = _width_in(b, h // 2, h)
            return bw > tw * 1.15, 0.6
        if feat == 'hook_or_curve_bot':

            bot = b[int(h * 0.60):]
            return np.sum(cv2.Canny(bot, 50, 150) > 0) > 15, 0.6
        if feat == 'tail_any' or feat == 'has_tail':

            cnts, _ = cv2.findContours(b, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if len(cnts) <= 1: return False, 0.0
            areas = [cv2.contourArea(c) for c in cnts]
            return sum(1 for a in areas if a < max(areas) * 0.35) >= 1, 0.6
        if feat == 'tail_at_top':
            return _tail_in(img, 'top'), 0.6
        if feat == 'tail_at_bottom' or feat == 'tail_bot':
            return _tail_in(img, 'bot'), 0.6
        if feat == 'has_crossbar':

            return F.hline(img, 'mid') or F.hline(img, 'any'), 0.6
        if feat == 'dual_blob':

            upper = b[:int(h * 0.50)]
            lower = b[int(h * 0.50):]
            u_cc = np.sum(upper > 0); l_cc = np.sum(lower > 0)
            return u_cc > 50 and l_cc > 50, 0.65
        if feat == 'round_right':

            right = b[:, w // 3:]
            cnts, _ = cv2.findContours(right, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not cnts: return False, 0.0
            c = max(cnts, key=cv2.contourArea)
            a = float(cv2.contourArea(c)); p = cv2.arcLength(c, True)
            return (4 * np.pi * a / (p ** 2)) > 0.35 if p > 0 else False, 0.6
        if feat == 'sharp_corners':
            g = b; d = cv2.cornerHarris(g, 2, 3, 0.04)
            return np.sum(d > 0.01 * d.max()) > 5, 0.6
        if feat == 'two_stack':

            mid_row = np.sum(b > 0, axis=1)
            gap_rows = np.where(mid_row < 5)[0]
            if len(gap_rows) < 2: return False, 0.3

            mid_start, mid_end = h // 4, 3 * h // 4
            mid_gaps = [r for r in gap_rows if mid_start <= r <= mid_end]
            return len(mid_gaps) >= 2, 0.55



        if feat == 'enclosed_or_round':
            return F.has_enclosed(img) or F.roundish(img), 0.65

        if feat == 'no_dual_vert':
            return not F.dual_vert(img), 0.6

        if feat == 'vert_or_diag':
            return F.has_vert_line(img) or F.diag_any(img), 0.6

        if feat == 'has_enclosed_loose':

            inv = cv2.bitwise_not((img>127).astype(np.uint8)*255)
            n, labels, stats, _ = cv2.connectedComponentsWithStats(inv)
            if n < 3:

                return F.roundish(img), 0.5
            h, w = img.shape
            for i in range(1, n):
                area = stats[i, cv2.CC_STAT_AREA]
                cw = stats[i, cv2.CC_STAT_WIDTH]; ch = stats[i, cv2.CC_STAT_HEIGHT]
                if area > h*w*0.015 and cw < w-1 and ch < h-1:
                    return True, 0.75
            return False, 0.0


        if feat == 'roundish_any':

            cnts,_=cv2.findContours((img>127).astype(np.uint8)*255,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
            if not cnts: return False,0.0
            c=max(cnts,key=cv2.contourArea); a=float(cv2.contourArea(c)); p=cv2.arcLength(c,True)
            circ=4*np.pi*a/(p**2) if p>0 else 0
            return circ>0.28, 0.55

        if feat == 'two_curves':

            h=img.shape[0]
            top=img[:int(h*0.48)]; bot=img[int(h*0.52):]
            t_edges=cv2.Canny(top,50,150); b_edges=cv2.Canny(bot,50,150)
            t_d=np.sum(t_edges>0)/max(t_edges.size,1); b_d=np.sum(b_edges>0)/max(b_edges.size,1)
            return t_d>0.03 and b_d>0.03, 0.6


        if feat == 'has_ink_top':
            return np.sum(img[:int(img.shape[0]*0.35)]>127) > 20, 0.6

        if feat == 'right_side_curved':

            h,w=img.shape; right=img[:,w//2:]
            cnts,_=cv2.findContours(right,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
            if not cnts: return False,0.3
            c=max(cnts,key=cv2.contourArea); a=float(cv2.contourArea(c)); p=cv2.arcLength(c,True)
            circ=4*np.pi*a/(p**2) if p>0 else 0
            return circ>0.22, 0.55

        if feat == 'curved_shape':

            cnts,_=cv2.findContours((img>127).astype(np.uint8)*255,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
            if not cnts: return False,0.0
            c=max(cnts,key=cv2.contourArea); a=float(cv2.contourArea(c)); p=cv2.arcLength(c,True)
            circ=4*np.pi*a/(p**2) if p>0 else 0

            return circ>0.20, 0.55

        if feat == 'multi_stroke':

            cs=np.sum((img>127).astype(np.uint8)*255>0,axis=0)
            peaks=0; prev=False
            for x in cs:
                if x>3 and not prev: peaks+=1
                prev=x>3
            return peaks>=3, 0.6

        if feat == 'not_narrow':
            ar=F.aspect(img)
            return ar>0.55, 0.6

        if feat == 'wider_than_tall':
            ar=F.aspect(img)
            return ar>0.90, 0.6

        if feat == 'has_ink_everywhere':

            cs=np.sum((img>127).astype(np.uint8)*255>0,axis=0)
            active=np.where(cs>0)[0]
            if len(active)<2: return False,0.3
            span=active[-1]-active[0]
            return span>img.shape[1]*0.75, 0.6

        if feat == 'apex_top':
            top = b[:int(h * 0.35)]; cs = np.sum(top > 0, axis=0)
            act = np.where(cs > 0)[0]
            if len(act) < 2: return False, 0.3
            mid = w / 2; sc = act[0] < mid < act[-1]
            bot = b[int(h * 0.65):]; bc = np.where(np.sum(bot > 0, axis=0) > 0)[0]
            tw = act[-1] - act[0] if len(act) > 1 else 0
            bw = bc[-1] - bc[0] if len(bc) > 1 else 0
            return (sc and (tw < bw * 0.9 if bw > 5 else True)), 0.65
        if feat == 'wider_at_bottom':
            top = b[:int(h * 0.35)]; bot = b[int(h * 0.65):]
            tw_cs = np.sum(top > 0, axis=0); bw_cs = np.sum(bot > 0, axis=0)
            ta = np.where(tw_cs > 0)[0]; ba = np.where(bw_cs > 0)[0]
            if len(ta) < 2 or len(ba) < 2: return False, 0.3
            tw = ta[-1] - ta[0]; bw = ba[-1] - ba[0]
            return bw > tw * 1.12, 0.6
        if feat == 'crossbar_mid':
            band = b[int(h * 0.35):int(h * 0.60)]
            me = 0
            for i in range(band.shape[0]):
                rs = np.sum(band[i] > 0)
                if rs > w * 0.12:
                    co = np.where(band[i] > 0)[0]
                    if len(co) > 1: me = max(me, co[-1] - co[0])
            return me > w * 0.20, 0.6

        print(f'  [WARN] Unknown feature: {feat}')
        return False, 0.0
    except Exception as e:
        print(f'  [ERR] {feat}: {e}')
        import traceback; traceback.print_exc()
        return False, 0.0


def _circ_fallback(img):
    """Fallback circularity check for C-shape when roundish is too strict."""
    cnts, _ = cv2.findContours((img > 127).astype(np.uint8) * 255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts: return False
    c = max(cnts, key=cv2.contourArea); a = float(cv2.contourArea(c)); p = cv2.arcLength(c, True)
    return (4 * np.pi * a / (p ** 2)) > 0.28 if p > 0 else False


def F_diag_count_img(region, min_len=4):
    """Diagonal count on a sub-image region."""
    if region.size == 0: return 0
    edges = cv2.Canny(region, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 4, min_len, 2)
    if lines is None: return 0
    c = 0
    for l in lines:
        dx = abs(l[0][2] - l[0][0]); dy = abs(l[0][3] - l[0][1])
        if dx > 2 and dy > 2: c += 1
    return c



F.diag_count_img = staticmethod(F_diag_count_img)


def _width_in(b, y_start, y_end):
    """Get width of ink in a horizontal band."""
    band = b[y_start:y_end]
    cs = np.sum(band > 0, axis=0)
    active = np.where(cs > 0)[0]
    return active[-1] - active[0] if len(active) > 1 else 0


def _tail_in(img, reg):
    b = (img > 127).astype(np.uint8) * 255; h = b.shape[0]
    roi = b[:int(h * 0.35)] if reg == 'top' else b[int(h * 0.65):]
    cnts, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return len(cnts) >= 2






def score_v8(user_img, char_target='A'):
    char = char_target
    rules = RULES.get(char) or RULES.get(char.upper()) or RULES.get(char.lower())
    if rules is None:
        return _generic(user_img, char), {'method': 'generic'}

    details = {}
    px = F.px(user_img)
    details['px'] = px








    h, w = user_img.shape
    if max(h, w) >= 100:

        close_kernel = np.ones((13, 13), np.uint8)
        closed = cv2.morphologyEx(user_img, cv2.MORPH_CLOSE, close_kernel)

        erode_kernel = np.ones((5, 5), np.uint8)
        img_for_features = cv2.erode(closed, erode_kernel, iterations=1)
        details['preprocessed'] = 'closed+eroded'
    else:
        img_for_features = user_img
        details['preprocessed'] = 'none'




    min_px = rules.get('min_px', 60)
    if px < min_px // 3:
        details['reason'] = f'tiny ({px}px)'
        return 0, details
    if px < min_px:
        details['reason'] = f'small ({px}<{min_px})'
        return 0, details



    integrity = _shape_integrity_check(img_for_features, char)
    if integrity['reject']:
        details['reason'] = integrity['reason']
        details['integrity'] = 'FAIL'
        return integrity['score'], details


    required = rules.get('required', [])
    req_pass, feats = 0, {}
    for f in required:
        ok, _ = check(f, img_for_features)
        feats[f] = ok
        if ok: req_pass += 1
    details['feats'] = feats
    details['req'] = f'{req_pass}/{len(required)}'
    nr = len(required)
    rr = req_pass / max(nr, 1)


    anti = rules.get('anti', [])
    anti_hits, anti_pen = [], 0
    for f in anti:
        ok, _ = check(f, img_for_features)
        if ok:
            anti_hits.append(f)
            anti_pen += 6
    details['anti'] = anti_hits


    bonus_list = rules.get('bonus', [])
    bonus_p = 0
    for f in bonus_list:
        ok, _ = check(f, img_for_features)
        if ok:
            bonus_p += 1
            anti_pen -= 3
    details['bonus'] = f'{bonus_p}/{len(bonus_list)}'


    critical_feats = {'has_enclosed', 'apex_top'}
    critical_fail = any(f in critical_feats and not feats.get(f, False) for f in required)

    if req_pass == nr and nr > 0:


        score = 82
        score += int(_cov(px) * 1.0)
        score += int(_cen(img_for_features) * 0.8)
        if F.complexity(img_for_features) > 1.4: score += 6
        score -= min(anti_pen, 14)
    elif critical_fail:


        score = 5 + int(rr * 12)
        score -= min(anti_pen, 12)
        score = min(score, 25)
    elif req_pass >= max(1, nr // 2):


        score = 22 + int(rr * 24)
        score += int(_cov(px) * 0.6)
        score -= min(anti_pen, 12)
        score = min(score, 55)
    else:


        score = int(rr * 10)
        score -= min(anti_pen, 8)
        score = min(score, 20)

    final = max(0, min(100, round(score, 1)))
    details['score'] = final
    return final, details








_LINE_CHARS = {'I', 'l', '1', 'i'}


def _shape_integrity_check(img, char_target):
    """
    Pre-filter: reject inputs that are clearly not the target character.
    Returns dict with 'reject' (bool), 'reason' (str), 'score' (int).
    """
    h, w = img.shape
    b = (img > 127).astype(np.uint8) * 255
    px = int(np.sum(b > 0))


    pts = np.argwhere(img > 127)
    if len(pts) < 5:
        return {'reject': True, 'reason': 'almost_empty', 'score': 0}
    ys, xs = zip(*pts)
    bb_w = max(xs) - min(xs) + 1
    bb_h = max(ys) - min(ys) + 1
    aspect = float(bb_w) / max(bb_h, 1)



    if bb_w < 20 and bb_h < 20:
        return {'reject': True, 'reason': f'dot_like({bb_w}x{bb_h})', 'score': 0}


    if char_target not in _LINE_CHARS:


        if aspect > 8.0 or aspect < 0.10:
            return {'reject': True, 'reason': f'line_like(ar={aspect:.1f})', 'score': 0}

        if bb_h < 10 or bb_w < 10:
            return {'reject': True, 'reason': f'thin({bb_w}x{bb_h})', 'score': 0}



    enclosed_chars = {'O','Q','D','P','R','B','0','6','8','9','a','b','d','e','o','g'}
    if char_target in enclosed_chars or char_target.upper() in enclosed_chars:

        area = bb_w * bb_h
        density = px / max(area, 1)
        if density < 0.08:
            return {'reject': True, 'reason': f'sparse_enclosed(d={density:.2f})', 'score': 0}



    n_comp, _ = cv2.connectedComponents(b)
    if n_comp > 15:
        return {'reject': True, 'reason': f'too_fragmented({n_comp}_parts)', 'score': 2}

    return {'reject': False, 'reason': 'ok', 'score': -1}


def _cov(px):

    if px < 80: return 0
    if px < 200: return 3
    if px < 500: return 6
    if px < 1200: return 9
    if px < 2500: return 12
    return 14

def _cen(img):
    o = F.center_off(img)

    if o < 20: return 5
    if o < 35: return 3
    if o < 50: return 1
    return 0

def _generic(img, char):
    px = F.px(img)
    if px < 30: return 0
    if px < 80: return 12
    return min(45, px // 10)
